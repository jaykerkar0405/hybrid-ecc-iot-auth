#!/usr/bin/env python3
"""Layer A: the base paper's published results as one machine-readable file (no simulation, no fitting).
Tables III-VI come from research/paper_audit/paper_tables.py (transcribed from 300-DPI renders of the PDF);
Figs. 1-3 are the exact bar heights extracted from the PDF vector paths (targets/fig_targets.json)."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "paper_audit"))
import paper_tables as P
fig = json.load(open(HERE.parent / "targets" / "fig_targets.json"))
out = {
  "source": "Al-Rasheed et al., IEEE Trans. Consum. Electron. 72(2):4483-4491, 2026, DOI 10.1109/TCE.2026.3662053",
  "note": "values exactly as published; None = '-' in the paper. Figs. are bar heights read from the PDF vector paths.",
  "table_II_environment": {"area_m": "1500x1500", "simulator": "OMNeT++", "devices": "100-1000", "servers": "5% (one per hundred devices)",
                           "sampling_interval_us": 15, "bandwidth_Mbps": 10, "tx_mW": 75.6, "rx_mW": 75.6, "range_m": "500-800",
                           "packet_size": "128 Kbps (sic)", "handoff_ns": 10, "speed_max_kmh": 160, "adversary": "randomly generated"},
  "table_III_ms": P.T3,
  "table_IV_comm_bits": {k: dict(zip(("messages", "user", "device", "server", "total"), v)) for k, v in P.T4.items()},
  "table_V_ops": P.T5,
  "table_VI_storage_bits": {k: dict(zip(("server", "device"), v)) for k, v in P.T6.items()},
  "claims": {"abstract": "~17% communication, ~21% processing, ~12% storage reduction", "text_comm_bits": 264, "text_messages": 2},
  "figures": {k: {kk: fig[k][kk] for kk in ("x", "series", "censored") if kk in fig[k]} for k in ("fig1", "fig2", "fig3")},
  "figure_axis_labels": {"fig1": "Communication Overhead (%), caption says processing", "fig2": "Communication Cost (bits)", "fig3": "Storage Overhead (%)"},
}
(HERE / "published_baseline.json").write_text(json.dumps(out, indent=1), encoding="utf8")
print("wrote", HERE / "published_baseline.json")
