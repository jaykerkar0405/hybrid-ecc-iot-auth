"""BR-1.3, BR-2.2, BR-3.2: cost-model stubs for the schemes the source
paper compares against.

Every number in reference_data.py is a **reference value copied verbatim
from the source paper** (Tables III, IV, V, VI) -- it is not independently
re-derived or re-implemented. Full re-implementation of all nine external
protocols is out of scope for v1 (PRD Section 13, V2 backlog); see
bench/report.py for how these values are combined with the paper's own
Table III timing constants to produce the "paper-assumed" analytical
comparison alongside our real, measured numbers for the proposed scheme.
"""

from .reference_data import (
    BASELINE_COMMUNICATION,
    BASELINE_COMPUTATION_FORMULAS,
    BASELINE_STORAGE,
    TABLE_III_CONSTANTS,
    evaluate_formula,
)

__all__ = [
    "BASELINE_COMMUNICATION",
    "BASELINE_COMPUTATION_FORMULAS",
    "BASELINE_STORAGE",
    "TABLE_III_CONSTANTS",
    "evaluate_formula",
]
