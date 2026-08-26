"""Typed protocol-layer exceptions (FR-5.2, SEC-01..SEC-08).

These wrap lower-level crypto failures (e.g. cryptography.exceptions.InvalidTag)
and add protocol-specific rejection reasons so callers -- and the adversarial
test suite -- can distinguish *why* an authentication attempt was rejected.
"""

from __future__ import annotations


class AuthenticationError(Exception):
    """Base class for all authentication-phase rejections."""


class IntegrityError(AuthenticationError):
    """AEAD tag / MAC verification failed (SEC-03: tampered ciphertext or MAC)."""


class ReplayDetected(AuthenticationError):
    """A pseudonym/nonce combination was already seen (SEC-01, SEC-02)."""


class UnknownPeerError(AuthenticationError):
    """The incoming pseudonym does not resolve to any known, registered peer."""


class BlockedEntity(AuthenticationError):
    """Entity is on the local block-list after 3 consecutive failed attempts
    (Section II, FR-5.6, SEC-05)."""


class CoverageError(AuthenticationError):
    """Access-control gate Allow_ij(t) = cov_ij(t) AND Auth_ij(t) failed
    because the coverage predicate was False (Eq. 23, FR-7, SEC-08)."""


class SessionTimeoutError(AuthenticationError):
    """The per-session handshake window (FR-5.5) elapsed before completion."""


class OfflinePhaseViolation(Exception):
    """Raised (in tests) if TA registration code attempts network I/O, which
    the paper's threat model assumes is impossible (Section III-M, FR-2.3)."""
