"""FR-1.1: Elliptic curve group -- NIST P-256 (secp256r1) via `cryptography`.

Satisfies the paper's abstract group description (F_q, E/F_q, G) of prime
order n (Section IV-A). All ECC operations in this protocol are confined to
the offline phase: deriving each entity's long-term secret lambda_X (Eq. 8)
and, optionally, its public point P_X = lambda_X * G (Eq. 1, 2). The online
authentication path (Section III-E..H) uses only symmetric primitives.
"""

from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

#: The curve used throughout this implementation (FR-1.1).
CURVE = ec.SECP256R1()

#: Order n of the secp256r1 base point group (NIST P-256).
#: Public, standardized constant -- see FIPS 186-4 / SEC2.
CURVE_ORDER = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551


def reduce_mod_n(value: int) -> int:
    """Reduce an arbitrary integer into Z*_n = {1, ..., n-1} (Eq. 8 domain).

    A zero result (probability ~2^-256, cryptographically negligible) is
    mapped to 1 rather than raising, so this function is a total map onto
    the *valid* secret-key range and callers never need special-case it.
    """
    r = value % CURVE_ORDER
    return r if r != 0 else 1


def scalar_to_public_point(scalar: int) -> bytes:
    """Compute scalar * G and return it as uncompressed SEC1 point bytes.

    Used for the optional public point P_X = lambda_X * G (Eq. 1, 2, FR-2.2).
    """
    scalar = reduce_mod_n(scalar)
    private_key = ec.derive_private_key(scalar, CURVE)
    public_key = private_key.public_key()
    return public_key.public_bytes(
        encoding=Encoding.X962,
        format=PublicFormat.UncompressedPoint,
    )
