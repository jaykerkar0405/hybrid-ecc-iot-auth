"""FR-1.2: Hash function wrappers H1, H2, H3 -- SHA-256 (paper's
"Instantiation Notes": H_{1,2,3} via SHA-256).

- H1 (Eq. 8): derives an entity's long-term ECC secret lambda_X from its
  identity and the TA master secret.
- H2 (Eq. 11): derives an epoch-rotated, unlinkable pseudonym PID_{Vi,t}.
- H3 (Eq. 24): optional rekey-epoch binder, used only by the v2 rekey stub.
"""

from __future__ import annotations

import hashlib
import struct

from .curve import reduce_mod_n


def _sha256(*parts: bytes) -> bytes:
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.digest()


def h1_derive_secret(identity: bytes, master_secret: bytes) -> int:
    """H1(ID_X || s) mod n -> lambda_X (Eq. 8)."""
    digest = _sha256(identity, master_secret)
    return reduce_mod_n(int.from_bytes(digest, "big"))


def h2_pseudonym(lam: int, epoch: int) -> bytes:
    """H2(lambda_Vi || t) -> PID_{Vi,t} (Eq. 11)."""
    lam_bytes = lam.to_bytes(32, "big")
    epoch_bytes = struct.pack(">Q", epoch)
    return _sha256(lam_bytes, epoch_bytes)


def h3_rekey_binder(update_index: int) -> bytes:
    """H3(u) -> rekey epoch binder (Eq. 24, v2 rekey stub only)."""
    return _sha256(struct.pack(">Q", update_index))
