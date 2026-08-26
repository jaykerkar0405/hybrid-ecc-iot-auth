"""Reference values transcribed verbatim from Al-Rasheed et al. (2026),
Tables III, IV, V, and VI. Source: docs/base_paper.pdf.

These are the paper's own reported/assumed numbers, not measurements taken
by this project. Row labels are kept exactly as printed in each table,
including the source paper's own apparent inconsistency of citing ref
[17] (S. Challa et al. in the References list) as "Wazid et al. [17]" in
Tables IV/VI while Table V lists *both* a "Challa et al. [17]" row and a
separate "Wazid et al. [17]" row with different formulas -- we do not
silently correct this; "Challa et al." appears only in Table V (the paper
itself does not compare it in Tables IV or VI).
"""

from __future__ import annotations

#: Table III: reference per-operation timing constants (milliseconds),
#: as *assumed* (not measured) by the paper, calibrated for
#: resource-constrained embedded hardware (PRD 6.2).
TABLE_III_CONSTANTS = {
    "TECM": 17.1,  # Scalar Multiplication of ECC
    "TC": 0.32,  # Chaotic Map (Chebyshev Operation)
    "TSE_D": 5.6,  # Encryption/Decryption (Symmetric)
    "TH": 0.32,  # Hash Function (one-way SHA-1)
    "Tfe": 17.1,  # Fuzzy Extraction Operation
}


def evaluate_formula(formula: str, constants: dict[str, float] | None = None) -> float:
    """Evaluate one of the Table V operation-count formula strings (e.g.
    "2*TH + 2*TSE_D") using `constants` (defaults to Table III's own
    assumed values). Restricted eval: only the four whitelisted constant
    names are exposed, no builtins."""
    consts = constants if constants is not None else TABLE_III_CONSTANTS
    return float(eval(formula, {"__builtins__": {}}, dict(consts)))  # noqa: S307 - restricted namespace, fixed formula strings we authored


#: Table IV: communication cost, in bits.
#: Columns: number_of_messages, user_bits, device_bits, server_bits, total_bits.
#: "Proposed Scheme" row is included for direct citation/comparison, but the
#: bench report treats our own scheme's communication cost as *measured*
#: (bench/proposed.py), not taken from this table.
BASELINE_COMMUNICATION = {
    "Proposed Scheme (paper-reported)": {"messages": 4, "user_bits": None, "device_bits": 512, "server_bits": 512, "total_bits": 1024},
    "Porambage et al. [11]": {"messages": 4, "user_bits": 768, "device_bits": 768, "server_bits": 1824, "total_bits": 3360},
    "Turkanovic et al. [12]": {"messages": 4, "user_bits": 672, "device_bits": 576, "server_bits": 1472, "total_bits": 2720},
    "Dhillon and Karla [13]": {"messages": 4, "user_bits": 992, "device_bits": 512, "server_bits": 1024, "total_bits": 2528},
    "Cheng and Le [14]": {"messages": 4, "user_bits": 672, "device_bits": 512, "server_bits": 1088, "total_bits": 2272},
    "Jiang et al. [15]": {"messages": 4, "user_bits": 512, "device_bits": 1056, "server_bits": 384, "total_bits": 1952},
    "Shuai et al. [16]": {"messages": 4, "user_bits": 864, "device_bits": 544, "server_bits": 960, "total_bits": 2368},
    "Wazid et al. [17]": {"messages": 4, "user_bits": 736, "device_bits": 512, "server_bits": 1344, "total_bits": 2592},
    "Sadhukhan et al. [18]": {"messages": 4, "user_bits": 320, "device_bits": 768, "server_bits": 512, "total_bits": 1600},
    "Fakroon et al. [19]": {"messages": 4, "user_bits": 800, "device_bits": 416, "server_bits": 1088, "total_bits": 2304},
}

#: Table V: computational cost, as symbolic operation-count formulas
#: (evaluate with evaluate_formula() + TABLE_III_CONSTANTS or your own
#: measured per-primitive costs). Columns: user_client, device, server.
BASELINE_COMPUTATION_FORMULAS = {
    "Proposed scheme (paper-reported)": {"user_client": "2*TH + 2*TSE_D", "device": "2*TH + 2*TSE_D", "server": "4*TH + 5*TECM"},
    "Challa et al. [17]": {"user_client": "1*Tfe + 5*TH + 5*TSE_D", "device": "3*TH + 4*TECM", "server": "4*TH + 5*TECM"},
    "Turkanovic et al. [12]": {"user_client": "7*TH", "device": "7*TH", "server": "5*TH"},
    "Porambage et al. [11]": {"user_client": "8*TH + 4*TECM", "device": "10*TH + 11*TECM", "server": "5*TH + 8*TECM"},
    "Dhillon and Karla [13]": {"user_client": "8*TH", "device": "6*TH", "server": "8*TH"},
    "Cheng and Le [14]": {"user_client": "9*TH + 2*TECM", "device": "5*TH + 2*TECM", "server": "7*TH"},
    "Shuai et al. [16]": {"user_client": "6*TH + 1*TECM", "device": "3*TH + 1*TECM", "server": "7*TH + 1*TECM"},
    "Jiang et al. [15]": {"user_client": "7*TH", "device": "5*TH", "server": "10*TH"},
    "Wazid et al. [17]": {"user_client": "1*Tfe + 13*TH + 2*TSE_D", "device": "4*TH + 2*TSE_D", "server": "5*TH + 4*TSE_D"},
    "Sadhukhan et al. [18]": {"user_client": "2*TH + 1*TECM + 2*TSE_D", "device": "1*TH + 1*TECM + 2*TSE_D", "server": "2*TH + 4*TECM"},
}

#: Table VI: storage cost, in bytes. Columns: server_bytes, device_bytes.
#: Das et al.'s server cost includes an unresolved "+CH*" term in the
#: source paper (asterisk left undefined) -- kept as a string, not a
#: number, and excluded from any numeric comparison/chart.
BASELINE_STORAGE = {
    "Proposed Scheme (paper-reported)": {"server_bytes": 320, "device_bytes": 320},
    "Turkanovic et al. [12]": {"server_bytes": 768, "device_bytes": 512},
    "Dhillon and Karla [13]": {"server_bytes": 640, "device_bytes": 512},
    "Das et al. [20]": {"server_bytes": "768+CH*", "device_bytes": None},
    "Wazid et al. [17]": {"server_bytes": 576, "device_bytes": 512},
    "Sadhukhan et al. [18]": {"server_bytes": 480, "device_bytes": 356},
    "Fakroon et al. [19]": {"server_bytes": 704, "device_bytes": 1056},
}
