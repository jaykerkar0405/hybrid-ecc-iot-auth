"""FR-8.1 / NG5: stub interface for Eq. 24 TA-assisted periodic rekeying.

k*_ij^(u+1) = KDF(k*_ij^(u) || H3(u))

Unimplemented in v1 (see PRD Section 13, V2/Backlog). This stub exists so
the architecture doesn't need rework later: entity.py's pairwise-root cache
already exposes `invalidate_pairwise_root` as the hook a real
implementation of `rekey` would call after installing a new root.
"""

from __future__ import annotations


def rekey(*_args, **_kwargs) -> None:
    raise NotImplementedError(
        "TA-assisted rekeying (Eq. 24, Section III-N) is a v2 backlog item; "
        "see docs/product_requirements_document.pdf Section 13."
    )
