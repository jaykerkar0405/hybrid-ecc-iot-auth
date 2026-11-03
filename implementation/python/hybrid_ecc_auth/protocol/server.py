# Copyright (c) 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur
# SPDX-License-Identifier: Apache-2.0
"""Server-side state machine (FR-5): resolves the incoming pseudonym
(FR-4.2), verifies M1 (Eq. 12-15), derives the session key (Eq. 16), and
builds M2 (Eq. 17-19). See protocol/device.py for the shared wire-plaintext
layout this module and device.py both implement.
"""

from __future__ import annotations

from dataclasses import dataclass

from cryptography.exceptions import InvalidTag

from ..crypto import aead
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
from .resolution import LinearScan, Resolver


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
        resolver: Resolver | None = None,
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
        # Pseudonym resolution is not specified by the base paper; the
        # default LinearScan is the original behaviour of this method.
        # See protocol/resolution.py for the alternatives.
        self.resolver = resolver if resolver is not None else LinearScan()
        self.resolver.attach(self.credential.peer_secrets, self.session_log)

    def resolve_pseudonym(self, pid: bytes) -> tuple[str, int]:
        """FR-4.2: resolve an incoming pseudonym to a known device identity
        and epoch. Delegates to the configured resolver; the default
        LinearScan probes every enrolled peer over its bounded epoch window
        with a constant-time compare per candidate (the search itself is
        not constant-time across peers; timing side-channels are out of
        scope for this PoC -- see docs/design.md).
        """
        return self.resolver.resolve(pid)

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

        self.resolver.accept(peer_identity, epoch, n_i)
        self.session_log.record_success(peer_identity)

        n_j = generate_nonce(self.nonce_bits)
        session_key = derive_session_key(k_star, n_i, n_j, epoch)

        aad = msg1.pid + n_i
        plaintext2 = n_j + epoch.to_bytes(8, "big")
        gcm_nonce2, ciphertext2, tag2 = aead.encrypt(k_star, plaintext2, aad=aad)
        msg2 = Message2(server_id=self.credential.identity, gcm_nonce=gcm_nonce2, ciphertext=ciphertext2, tag=tag2)

        return AuthResult(response_bytes=msg2.to_bytes(), session_key=session_key, peer_identity=peer_identity)
