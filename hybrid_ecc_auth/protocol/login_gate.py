"""FR-6: Login Phase (optional, togglable pre-authentication gate).

Implements the Section II-B login check -- MAC address + H_D = h(MAC_D ||
PWD) -- as a pre-check that can run *before* the Section III nonce-based
mutual authentication exchange (protocol/device.py, protocol/server.py).

This is deliberately kept separate from, and disabled by default relative
to, the core authentication phase: the source paper treats login and
mutual authentication as sequential phases, and the design decision
documented in the PRD is to rely on Section III's nonce-based exchange
(with fresh N_i/N_j per session) as the actual security boundary. The
login gate's static H_D is not refreshed per session and is therefore not
a replay-resistant credential on its own -- see the PRD's "Design
decision" callout.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass


def compute_login_hash(mac_address: bytes, password: bytes) -> bytes:
    """H_D = h(MAC_D || PWD) (Section II-B)."""
    return hashlib.sha256(mac_address + password).digest()


@dataclass(frozen=True)
class LoginRequest:
    mac_address: bytes
    login_hash: bytes  # H_D


class LoginGate:
    """Optional pre-check gate (FR-6.1). Disabled (`enabled=False`) by
    default; toggle on to require a successful login-hash match before a
    device is permitted to proceed to the Section III authentication phase.
    """

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def build_request(self, mac_address: bytes, password: bytes) -> LoginRequest:
        return LoginRequest(mac_address=mac_address, login_hash=compute_login_hash(mac_address, password))

    def verify(self, request: LoginRequest, expected_password: bytes) -> bool:
        """Constant-time verification of a received login request against
        the server's stored password for that MAC address."""
        expected = compute_login_hash(request.mac_address, expected_password)
        return hmac.compare_digest(expected, request.login_hash)
