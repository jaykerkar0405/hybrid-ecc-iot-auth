#!/usr/bin/env python3
"""Recalculate the citation audit from curated evidence and existing PDF transcriptions.

Requires Python 3 and Poppler's pdfinfo/pdftotext. No network or simulator runs.
The source anchors check page locations, not the correctness of every transcription.
Run from any directory; --check compares fresh results with the saved artifacts.
"""

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import unicodedata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def read_json(path):
    return json.loads(path.read_text())


def reduction(proposed, comparator):
    return 100 * (comparator - proposed) / comparator


def normalize(value):
    return "".join(unicodedata.normalize("NFKC", value).split()).casefold()


def cost(ops, constants):
    return sum(count * constants[operation] for operation, count in (ops or {}).items())


def source_inventory():
    records = []
    for path in sorted((ROOT / "docs/references").glob("*.pdf")):
        info = subprocess.check_output(["pdfinfo", str(path)], text=True)
        title = re.search(r"^Title:\s*(.*)$", info, re.MULTILINE)
        records.append({
            "file": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "pages": int(re.search(r"^Pages:\s*(\d+)", info, re.MULTILINE)[1]),
            "metadata_title": title[1] if title else "",
        })
    return records


def check_anchors(evidence):
    checks = []
    for anchor in evidence["read_checks"]:
        path = ROOT / "docs/references" / anchor["file"]
        page = str(anchor["page"])
        content = subprocess.check_output(
            ["pdftotext", "-layout", "-f", page, "-l", page, str(path), "-"], text=True
        )
        missing = [s for s in anchor["phrases"] if normalize(s) not in normalize(content)]
        if missing:
            raise ValueError(f"Missing source anchor: {path.name} p.{page}: {missing}")
        checks.append({"file": anchor["file"], "page": anchor["page"],
                       "phrases_found": len(anchor["phrases"])})
    return checks


def figure_checks(base, jan):
    reductions, correspondences = {}, {}
    for key in ("fig1", "fig2", "fig3"):
        figure = base[key]
        proposed = figure["series"]["Proposed"]
        other = [values for name, values in figure["series"].items() if name != "Proposed"]
        best = [min(values[i] for values in other) for i in range(len(proposed))]
        average = [statistics.mean(values[i] for values in other) for i in range(len(proposed))]
        reductions[key] = {
            "axis_label": figure["y_label"],
            "mean_pointwise_reduction_vs_best_percent": statistics.mean(map(reduction, proposed, best)),
            "mean_pointwise_reduction_vs_mean_percent": statistics.mean(map(reduction, proposed, average)),
            "warning": "Digitized plotted heights; caption/axis units conflict. Not independent performance measurements.",
        }
    for base_key, jan_key in [("fig1", "fig5"), ("fig2", "fig7"), ("fig3", "fig8")]:
        b, j = base[base_key], jan[jan_key]
        diffs = {}
        for name, values in b["series"].items():
            diffs[name] = [v - j["series"][name][i] for i, v in enumerate(values)
                           if not b["censored"][name][i] and not j["censored"][name][i]]
        all_diffs = [v for values in diffs.values() for v in values]
        offset = statistics.mean(all_diffs)
        residuals = [v - offset for v in all_diffs]
        per_series = {name: statistics.mean(values) for name, values in diffs.items()}
        grouped = {"Proposed": per_series["Proposed"], "others": statistics.mean(
            [v for name, values in diffs.items() if name != "Proposed" for v in values])}
        group_residuals = [v - grouped["Proposed" if name == "Proposed" else "others"]
                           for name, values in diffs.items() for v in values]
        correspondences[f"{base_key}_vs_{jan_key}"] = {
            "uncensored_cells": len(all_diffs),
            "base_axis": b["y_label"], "jan_axis": j["y_label"],
            "uniform_offset_base_minus_jan": offset,
            "uniform_offset_rms_residual": math.sqrt(statistics.mean(v*v for v in residuals)),
            "uniform_offset_max_abs_residual": max(map(abs, residuals)),
            "per_series_offsets": per_series,
            "proposed_and_others_offsets": grouped,
            "two_group_offset_rms_residual": math.sqrt(statistics.mean(v*v for v in group_residuals)),
            "base_x": b["x"], "jan_x": j["x"],
        }
    return reductions, correspondences


def calculate():
    e = read_json(HERE / "evidence.json")
    spec = importlib.util.spec_from_file_location("paper_tables", ROOT / "research/paper_audit/paper_tables.py")
    tables = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tables)
    s = e["sadhukhan"]
    matched_comm = [name for name, row in s["communication_table5"].items()
                    if list(tables.T4[name]) == row]
    matched_storage = [name for name, row in s["storage_table6"].items()
                       if list(tables.T6[name]) == row]
    if len(matched_comm) != 9 or len(matched_storage) != 5 or s["constants_ms"] != tables.T3:
        raise ValueError("Source-to-BASE correspondence changed; review the evidence")

    headlines = {}
    for include_jiang in (True, False):
        names = [name for name in tables.T4 if name != "Proposed scheme"
                 and (include_jiang or not name.startswith("Jiang"))]
        best_name = min(names, key=lambda name: tables.T4[name][4])
        prop = tables.T4["Proposed scheme"][4]
        role_costs = {name: {role: cost(ops, tables.T3) for role, ops in row.items()}
                      for name, row in tables.T5.items()
                      if include_jiang or not name.startswith("Jiang")}
        headlines["with_jiang" if include_jiang else "without_jiang"] = {
            "communication_comparators": len(names),
            "communication_best_comparator": best_name,
            "communication_reduction_vs_best_percent": reduction(prop, tables.T4[best_name][4]),
            "communication_reduction_vs_mean_percent": reduction(prop, statistics.mean(tables.T4[n][4] for n in names)),
            "processing_printed_model_ms": {
                name: {"device_and_server": row["device"] + row["server"],
                       "all_roles": sum(row.values())} for name, row in role_costs.items()
            },
        }
    headlines["storage"] = {
        "server_reduction_vs_smallest_printed_comparator_percent": reduction(320, 480),
        "device_reduction_vs_smallest_printed_comparator_percent": reduction(320, 356),
        "device_reduction_vs_corrected_32_plus_320_percent": reduction(320, 352),
        "warning": "Arithmetic on printed numbers only; server/device roles are not preserved from the source.",
    }

    rows = []
    for name, source in e["primary_operation_rows"].items():
        original, printed = source["ops"], tables.T5[name]
        for role in ("user", "device", "server"):
            rows.append({"scheme": name, "role": role,
                         "base_ops": json.dumps(printed[role], sort_keys=True),
                         "primary_ops": json.dumps(original[role], sort_keys=True),
                         "base_model_ms": round(cost(printed[role], tables.T3), 8),
                         "primary_model_ms": round(cost(original[role], tables.T3), 8),
                         "match": printed[role] == original[role],
                         "primary_file": source["file"],
                         "pdf_pages": ",".join(map(str, source["pdf_pages"])), "basis": source["basis"]})
    csv_file = io.StringIO(newline="")
    writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

    plots, affine = figure_checks(
        read_json(ROOT / "research/omnet_emulation/targets/fig_targets.json"),
        read_json(ROOT / "research/omnet_emulation/jan_compare/jan_targets.json"))
    results = {
        "scope": "Arithmetic and curated source comparison, not a protocol-security proof or independent hardware/simulation reproduction.",
        "source_page_checks": check_anchors(e),
        "sadhukhan_correspondences": {"timing_constants_matching": 5,
                                     "communication_rows_matching": matched_comm,
                                     "storage_numeric_rows_matching": matched_storage,
                                     "source_storage_headers": s["storage_headers"],
                                     "base_storage_headers": ["Server Storage", "Device Storage"]},
        "headline_checks": headlines,
        "primary_operation_comparisons": rows,
        "arithmetic_checks": {
            "sadhukhan_sensor_storage_reported": s["sensor_storage_reported_bits"],
            "sadhukhan_sensor_storage_terms_sum": sum(s["sensor_storage_terms_bits"]),
            "sadhukhan_message_reported_values_sum": sum(s["own_message_reported_bits"]),
            "sadhukhan_message_literal_terms_sum": sum(map(sum, s["own_message_terms_bits"])),
            "sadhukhan_table_total": s["own_table_total_bits"],
            "fakroon_message_sum": sum(e["fakroon"]["per_message_bits"]),
            "fakroon_gateway_storage_reported": e["fakroon"]["gateway_storage_reported_bits"],
            "fakroon_gateway_storage_terms_sum": sum(e["fakroon"]["gateway_storage_terms_bits"]),
            "challa_own_model_ms": sum(cost(ops, tables.T3) for ops in e["primary_operation_rows"]["Challa et al. [17]"]["ops"].values()),
            "challa_base_model_ms": sum(cost(ops, tables.T3) for ops in tables.T5["Challa et al. [17]"].values()),
            "ma_own_phase_bits_sum": sum(e["figure_comparators"]["Ma/Zhanfei"]["phase_bits"]),
            "ma_jan_bits": e["figure_comparators"]["Ma/Zhanfei"]["jan_bits"],
            "gupta_own_bits": e["figure_comparators"]["Gupta"]["original_bits"],
            "gupta_jan_bits": e["figure_comparators"]["Gupta"]["jan_bits"],
            "alshawish_message_bytes_sum": sum(e["alshawish"]["message_bytes"]),
            "xie_own_model_ms": cost(e["xie"]["own_ops"], e["xie"]["constants_ms"]),
        },
        "digitized_plot_reductions": plots,
        "digitized_plot_correspondences": affine,
        "pending_jiang_changes_conclusion": False,
        "pending_jiang_note": "Excluding Jiang still leaves the table's communication reduction at 36%, the role/header errors, and hash-only rows cheaper under the printed cost model. Jiang's own row remains unverified.",
    }
    inputs = [HERE / "evidence.json", ROOT / "research/paper_audit/paper_tables.py",
              ROOT / "research/omnet_emulation/targets/fig_targets.json",
              ROOT / "research/omnet_emulation/jan_compare/jan_targets.json"]
    results["input_sha256"] = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in inputs}
    json_text = lambda value: json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    return {"results.json": json_text(results), "comparison.csv": csv_file.getvalue(),
            "source_inventory.json": json_text(source_inventory())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify saved outputs without writing")
    args = parser.parse_args()
    artifacts = calculate()
    for name, content in artifacts.items():
        path = HERE / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(f"Out-of-date artifact: {path}")
        else:
            path.write_text(content)
    print(f"{'Verified' if args.check else 'Wrote'} {len(artifacts)} artifacts; 16 PDF-page anchor checks passed.")


if __name__ == "__main__":
    main()
