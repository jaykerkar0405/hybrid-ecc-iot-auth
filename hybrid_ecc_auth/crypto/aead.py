"""FR-1.4: AES-256-GCM authenticated encryption (Enc/Dec + MAC in Eq. 13, 14,
17, 18). Per the paper's instantiation notes, the GCM tag doubles as the
message authenticator (mu_1, sigma_2), so `encrypt` returns the ciphertext
and tag as separate fields rather than one concatenated blob.

FR-1.5: nonce generation is CSPRNG-backed, security parameter ell = 128 bits
by default (configurable to 192/256 per Section III-K) -- this governs the
protocol-level freshness nonces N_i/N_j (see protocol/device.py,
protocol/server.py), not the 96-bit GCM IV below, which is a distinct
per-message wire-format value required by AES-GCM itself.
"""

from __future__ import annotations

import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

#: AES-256 key size in bytes.
KEY_LEN = 32
#: Standard AES-GCM IV size in bytes (96 bits), per NIST SP 800-38D.
GCM_NONCE_LEN = 12
#: GCM authentication tag size in bytes.
TAG_LEN = 16


def encrypt(key: bytes, plaintext: bytes, aad: bytes = b"") -> tuple[bytes, bytes, bytes]:
    """AES-256-GCM encrypt. Returns (gcm_nonce, ciphertext, tag).

    `tag` is the last TAG_LEN bytes of AESGCM's combined output and serves
    as the message's MAC (mu_1 / sigma_2 in the paper's equations).
    """
    if len(key) != KEY_LEN:
        raise ValueError(f"AES-256-GCM key must be {KEY_LEN} bytes, got {len(key)}")
    nonce = os.urandom(GCM_NONCE_LEN)
    combined = AESGCM(key).encrypt(nonce, plaintext, aad)
    ciphertext, tag = combined[:-TAG_LEN], combined[-TAG_LEN:]
    return nonce, ciphertext, tag


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, aad: bytes = b"") -> bytes:
    """AES-256-GCM decrypt + verify. Raises `cryptography.exceptions.InvalidTag`
    on any tampering (ciphertext, tag, aad, or nonce mismatch).

    Callers in protocol/ translate InvalidTag into the typed
    protocol.errors.IntegrityError per FR-5.2.
    """
    if len(key) != KEY_LEN:
        raise ValueError(f"AES-256-GCM key must be {KEY_LEN} bytes, got {len(key)}")
    combined = ciphertext + tag
    try:
        return AESGCM(key).decrypt(nonce, combined, aad)
    except InvalidTag:
        raise
