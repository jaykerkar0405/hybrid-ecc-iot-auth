"""Server-side state machine (FR-5): resolves the incoming pseudonym
(FR-4.2), verifies M1 (Eq. 12-15), derives the session key (Eq. 16), and
builds M2 (Eq. 17-19). See protocol/device.py for the shared wire-plaintext
layout this module and device.py both implement.
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag

from ..crypto import aead
from ..crypto.hashes import h2_pseudonym
from ..crypto.nonce import DEFAULT_NONCE_BITS, generate_nonce
from ..storage.session_log import SessionLog
from .entity import Entity, derive_session_key
from .errors import (
    BlockedEntity,
    CoverageError,
    IntegrityError,
    ReplayDetected,
    UnknownPeerError,
)
from .messages import Message1, Message2


@dataclass(frozen=True)
class AuthResult:
    response_bytes: bytes
    session_key: bytes
    peer_identity: str


class Server(Entity):
    def __init__(
        self,
        credential,
        *,
        coverage_predicate=None,
        nonce_bits: int = DEFAULT_NONCE_BITS,
        max_attempts: int = 3,
        forward_tolerance: int = 8,
        replay_lookback: int = 16,
    ):
        if credential.role != "server":
            raise ValueError(f"Server requires a credential with role='server', got {credential.role!r}")
        super().__init__(credential, coverage_predicate=coverage_predicate)
        self.nonce_bits = nonce_bits
        self.session_log = SessionLog(
            max_attempts=max_attempts,
            forward_tolerance=forward_tolerance,
            replay_lookback=replay_lookback,
        )

    def resolve_pseudonym(self, pid: bytes) -> tuple[str, int]:
        """FR-4.2: resolve an incoming pseudonym to a known device identity
        and epoch via a bounded local search, using a constant-time compare
        per candidate to avoid a trivial timing side-channel on any single
        comparison (the search itself is not constant-time across peers --
        see PRD 7.3, timing side-channels are out of scope for this PoC).
        """
        for peer_identity, peer_lam in self.credential.peer_secrets.items():
            for epoch in self.session_log.epoch_search_window(peer_identity):
                candidate_pid = h2_pseudonym(peer_lam, epoch)
                if hmac.compare_digest(candidate_pid, pid):
                    if self.session_log.is_stale_epoch(peer_identity, epoch):
                        raise ReplayDetected(
                            f"pseudonym for {peer_identity!r} reuses stale epoch {epoch}"
                        )
                    return peer_identity, epoch
        raise UnknownPeerError("pseudonym did not resolve to any known, in-window peer")

    def handle_auth_request(self, msg1_bytes: bytes) -> AuthResult:
        msg1 = Message1.from_bytes(msg1_bytes)

        peer_identity, epoch = self.resolve_pseudonym(msg1.pid)

        # FR-5.6 / SEC-05: fail fast, before the (heavier) AEAD decrypt.
        if self.session_log.is_blocked(peer_identity):
            raise BlockedEntity(f"{peer_identity} is block-listed after repeated failed attempts")

        if not self.coverage_ok(peer_identity):
            self.session_log.record_failure(peer_identity)
            raise CoverageError(f"{peer_identity} is out of coverage range (cov_ij(t) = False)")

        k_star = self.get_pairwise_root(peer_identity)
        try:
            plaintext = aead.decrypt(k_star, msg1.gcm_nonce, msg1.ciphertext, msg1.tag)
        except InvalidTag as exc:
            self.session_log.record_failure(peer_identity)
            raise IntegrityError(f"mu_1 verification failed for {peer_identity}") from exc

        epoch_bytes = plaintext[-8:]
        pid_in_plaintext = plaintext[:32]
        n_i = plaintext[32:-8]
        epoch_in_plaintext = int.from_bytes(epoch_bytes, "big")

        if pid_in_plaintext != msg1.pid or epoch_in_plaintext != epoch:
            self.session_log.record_failure(peer_identity)
            raise IntegrityError(f"decrypted PID/epoch does not match message header for {peer_identity}")

        self.session_log.accept_epoch(peer_identity, epoch)
        self.session_log.record_success(peer_identity)

        n_j = generate_nonce(self.nonce_bits)
        session_key = derive_session_key(k_star, n_i, n_j, epoch)

        aad = msg1.pid + n_i
        plaintext2 = n_j + epoch.to_bytes(8, "big")
        gcm_nonce2, ciphertext2, tag2 = aead.encrypt(k_star, plaintext2, aad=aad)
        msg2 = Message2(server_id=self.credential.identity, gcm_nonce=gcm_nonce2, ciphertext=ciphertext2, tag=tag2)

        return AuthResult(response_bytes=msg2.to_bytes(), session_key=session_key, peer_identity=peer_identity)
