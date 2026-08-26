"""Device-side state machine (FR-5): builds M1 (Eq. 12-15) and verifies M2
(Eq. 17-19), deriving the ephemeral session key (Eq. 16) on success.

Wire plaintext layout (this implementation's concrete instantiation of the
paper's abstract equations -- byte layout is not specified by the paper):

  M1 plaintext  = PID_{Vi,t} (32B) || N_i (nonce_bits/8 B) || t (8B, big-endian)
                  encrypted+MACed as one AES-GCM call -> (C1, mu_1) (Eq. 13/14)
  M2 plaintext  = N_j (?) || t (8B, big-endian), AAD = PID_{Vi,t} || N_i
                  encrypted+MACed as one AES-GCM call -> (C2, sigma_2) (Eq. 17/18)
                  (binding PID/N_i as AAD reproduces sigma_2's wider coverage
                  in Eq. 17 -- MAC_{k*}(PID||Ni||Nj||t) -- while only Nj||t
                  need to travel as ciphertext.)
"""

from __future__ import annotations

import time

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
    SessionTimeoutError,
    UnknownPeerError,
)
from .messages import Message1, Message2

DEFAULT_SESSION_TIMEOUT_SECONDS = 5.0


class _PendingSession:
    __slots__ = ("peer_identity", "epoch", "pid", "n_i", "k_star", "created_at")

    def __init__(self, peer_identity: str, epoch: int, pid: bytes, n_i: bytes, k_star: bytes, created_at: float):
        self.peer_identity = peer_identity
        self.epoch = epoch
        self.pid = pid
        self.n_i = n_i
        self.k_star = k_star
        self.created_at = created_at


class Device(Entity):
    def __init__(
        self,
        credential,
        *,
        coverage_predicate=None,
        nonce_bits: int = DEFAULT_NONCE_BITS,
        session_timeout: float = DEFAULT_SESSION_TIMEOUT_SECONDS,
        max_attempts: int = 3,
    ):
        if credential.role != "device":
            raise ValueError(f"Device requires a credential with role='device', got {credential.role!r}")
        super().__init__(credential, coverage_predicate=coverage_predicate)
        self.nonce_bits = nonce_bits
        self.session_timeout = session_timeout
        self.session_log = SessionLog(max_attempts=max_attempts)
        # Epoch t (FR-4.1) is tracked *per peer relationship*, not as one
        # global counter. Rationale: the server-side resolver (FR-4.2,
        # storage/session_log.py) bounds its search to a small window
        # around the last epoch it personally accepted for that peer,
        # starting at -1 (never seen) on first contact. A single global
        # counter shared across peers would desync that window as soon as
        # a device talked to a second server (its epoch would already be
        # far past that server's expected 0..forward_tolerance range).
        # Trade-off: two different peers' *first* contact with this device
        # both observe PID = H2(lambda_Vi || 0), so epoch alone does not
        # unlinkably distinguish "first contact with server A" from "first
        # contact with server B" -- only cross-session linkability *within*
        # one peer relationship is defended against (Section III-D's
        # unlinkability sketch is scoped to repeated observations of the
        # same conversation). Documented per PRD Section 12's flagged
        # epoch/clock-drift implementation decision.
        self._epoch: dict[str, int] = {}
        self._pending: dict[str, _PendingSession] = {}

    def current_pseudonym(self, peer_id: str, epoch: int | None = None) -> bytes:
        """PID_{Vi,t} = H2(lambda_Vi || t) (Eq. 11, FR-4.1) for the given
        peer relationship's current (or explicitly given) epoch."""
        if epoch is None:
            epoch = self._epoch.get(peer_id, 0)
        return h2_pseudonym(self.credential.lam, epoch)

    def build_auth_request(self, peer_id: str) -> bytes:
        """Build M1 (Eq. 12-15) for `peer_id` and return its wire bytes."""
        if self.session_log.is_blocked(peer_id):
            raise BlockedEntity(f"local policy has block-listed {peer_id!r} after repeated failures")
        if not self.coverage_ok(peer_id):
            raise CoverageError(f"{peer_id} is out of coverage range (cov_ij(t) = False)")

        k_star = self.get_pairwise_root(peer_id)
        epoch = self._epoch.get(peer_id, 0)
        pid = self.current_pseudonym(peer_id, epoch)
        n_i = generate_nonce(self.nonce_bits)

        plaintext = pid + n_i + epoch.to_bytes(8, "big")
        gcm_nonce, ciphertext, tag = aead.encrypt(k_star, plaintext)
        msg1 = Message1(pid=pid, gcm_nonce=gcm_nonce, ciphertext=ciphertext, tag=tag)

        self._pending[peer_id] = _PendingSession(
            peer_identity=peer_id, epoch=epoch, pid=pid, n_i=n_i, k_star=k_star, created_at=time.monotonic()
        )
        self._epoch[peer_id] = epoch + 1
        return msg1.to_bytes()

    def complete_auth(self, msg2_bytes: bytes) -> bytes:
        """Verify M2 (Eq. 17-19) and return the derived session key
        K_{ij,t} (Eq. 16, FR-5.4) on success."""
        msg2 = Message2.from_bytes(msg2_bytes)
        pending = self._pending.pop(msg2.server_id, None)
        if pending is None:
            raise UnknownPeerError(f"no pending authentication request for {msg2.server_id!r}")

        if time.monotonic() - pending.created_at > self.session_timeout:
            self.session_log.record_failure(pending.peer_identity)
            raise SessionTimeoutError(f"session with {pending.peer_identity} exceeded {self.session_timeout}s window")

        aad = pending.pid + pending.n_i
        try:
            plaintext = aead.decrypt(pending.k_star, msg2.gcm_nonce, msg2.ciphertext, msg2.tag, aad=aad)
        except InvalidTag as exc:
            self.session_log.record_failure(pending.peer_identity)
            raise IntegrityError("failed to verify server response (sigma_2/tag mismatch)") from exc

        epoch_bytes = plaintext[-8:]
        n_j = plaintext[:-8]
        epoch = int.from_bytes(epoch_bytes, "big")
        if epoch != pending.epoch:
            self.session_log.record_failure(pending.peer_identity)
            raise IntegrityError("server response epoch does not match the outstanding request")

        self.session_log.record_success(pending.peer_identity)
        return derive_session_key(pending.k_star, pending.n_i, n_j, pending.epoch)
