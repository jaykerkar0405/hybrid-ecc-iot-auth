"""Shared base for Device and Server (Section III model).

Holds: the TA-issued credential, the pluggable coverage predicate (FR-7),
a cache of derived pairwise symmetric roots (FR-3.2), and the pure Eq. 9 /
Eq. 16 / Eq. 23 math that both device.py and server.py need identically.
"""

from __future__ import annotations

from typing import Callable

from ..crypto.kdf import kdf

#: Domain-separation info strings for HKDF calls (avoids cross-purpose key
#: reuse between the pairwise root and the ephemeral session key).
_INFO_PAIRWISE_ROOT = b"hybrid-ecc-auth/pairwise-root/v1"
_INFO_SESSION_KEY = b"hybrid-ecc-auth/session-key/v1"


def derive_pairwise_root(lam_device: int, lam_server: int) -> bytes:
    """k*_ij = KDF(lambda_Vi || lambda_Rj) (Eq. 9).

    Device lambda is always concatenated first, server lambda second, so
    both sides -- each computing this independently and offline from their
    own TA-issued peer-key list (FR-3.1) -- arrive at the identical root
    regardless of which side (device or server) is doing the computing.
    """
    ikm = lam_device.to_bytes(32, "big") + lam_server.to_bytes(32, "big")
    return kdf(ikm, info=_INFO_PAIRWISE_ROOT)


def derive_session_key(k_star: bytes, n_i: bytes, n_j: bytes, epoch: int) -> bytes:
    """K_{ij,t} = KDF(k*_ij || Ni || Nj || t) (Eq. 16).

    Computed independently by both device (in complete_auth) and server (in
    handle_auth_request) once each side holds both nonces; the correctness
    property (Eq. 20, Pr[K_ij,t^(V) = K_ij,t^(R)] = 1) is exercised as an
    integration-test invariant in tests/property/test_session_key_agreement.py.
    """
    epoch_bytes = epoch.to_bytes(8, "big")
    ikm = k_star + n_i + n_j + epoch_bytes
    return kdf(ikm, info=_INFO_SESSION_KEY)


class Entity:
    """Common state machine base for Device and Server.

    `coverage_predicate` implements cov_ij(t) (Eq. 10, FR-7.1) as a
    pluggable callable `(peer_identity: str) -> bool`. It defaults to
    "always in range" (True) for the laptop PoC; a config flag can swap in
    a predicate that simulates out-of-range rejection for demo/testing
    (SEC-08).
    """

    def __init__(
        self,
        credential,
        *,
        coverage_predicate: Callable[[str], bool] | None = None,
    ):
        self.credential = credential
        self.coverage_predicate: Callable[[str], bool] = coverage_predicate or (lambda peer_identity: True)
        self._pairwise_root_cache: dict[str, bytes] = {}

    # -- FR-3.2: pairwise root caching, with invalidation hook for FR-8 ----

    def get_pairwise_root(self, peer_identity: str) -> bytes:
        """Return (and cache) k*_ij for `peer_identity`, computing it via
        Eq. 9 on first use. Raises KeyError if `peer_identity` is not in
        this entity's TA-issued peer-key list."""
        cached = self._pairwise_root_cache.get(peer_identity)
        if cached is not None:
            return cached

        peer_lam = self.credential.peer_secrets[peer_identity]
        if self.credential.role == "device":
            root = derive_pairwise_root(self.credential.lam, peer_lam)
        else:
            root = derive_pairwise_root(peer_lam, self.credential.lam)

        self._pairwise_root_cache[peer_identity] = root
        return root

    def invalidate_pairwise_root(self, peer_identity: str | None = None) -> None:
        """Drop cached root(s), e.g. after a TA-assisted rekey (FR-8, v2).
        With no argument, clears the entire cache."""
        if peer_identity is None:
            self._pairwise_root_cache.clear()
        else:
            self._pairwise_root_cache.pop(peer_identity, None)

    # -- FR-7: coverage / access control -----------------------------------

    def coverage_ok(self, peer_identity: str) -> bool:
        """cov_ij(t) (Eq. 10)."""
        return bool(self.coverage_predicate(peer_identity))

    def access_control_gate(self, peer_identity: str, auth_ok: bool) -> bool:
        """Allow_ij(t) = cov_ij(t) AND Auth_ij(t) (Eq. 23, SEC-08)."""
        return self.coverage_ok(peer_identity) and auth_ok
