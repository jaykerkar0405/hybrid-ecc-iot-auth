"""FR-1.5: CSPRNG nonce generation, ell = 128 bits by default (configurable
to 192/256 per Section III-K), for the protocol's freshness nonces N_i, N_j.
"""

from __future__ import annotations

import os

DEFAULT_NONCE_BITS = 128
SUPPORTED_NONCE_BITS = (128, 192, 256)


def generate_nonce(bits: int = DEFAULT_NONCE_BITS) -> bytes:
    if bits not in SUPPORTED_NONCE_BITS:
        raise ValueError(f"Unsupported nonce length {bits} bits; must be one of {SUPPORTED_NONCE_BITS}")
    return os.urandom(bits // 8)
