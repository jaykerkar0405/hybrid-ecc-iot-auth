"""FR-1.3: HKDF-SHA256 (RFC 5869) wrapper for Eq. 9, Eq. 16, and Eq. 24."""

from __future__ import annotations

from cryptography.hazmat.primitives import hashes as crypto_hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def kdf(ikm: bytes, *, info: bytes = b"", salt: bytes | None = None, length: int = 32) -> bytes:
    """HKDF-Extract-and-Expand over `ikm`, returning `length` key bytes.

    Used for:
      - Eq. 9:  k*_ij   = KDF(lambda_Vi || lambda_Rj)
      - Eq. 16: K_{ij,t} = KDF(k*_ij || Ni || Nj || t)
      - Eq. 24: k*_ij^(u+1) = KDF(k*_ij^(u) || H3(u))   (v2 rekey stub)
    """
    h = HKDF(
        algorithm=crypto_hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    )
    return h.derive(ikm)
