"""BR-4.1: renders the full benchmark results into a self-contained
Markdown report, a self-contained HTML report (charts embedded as base64
PNGs), a machine-readable JSON dump, and a CSV of the population-scaling
series (BR-2.3).
"""

from __future__ import annotations

import base64
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

_PROPOSED_COLOR = "#2a6f97"
_BASELINE_COLOR = "#a6a6a6"

METHODOLOGY_NOTE = """\
**Methodology and disclosed deviation (PRD Section 6.2).** The paper's
Tables IV-VI numbers come from an OMNeT++ simulation using *assumed*
per-operation timing constants (Table III: T_ECM = 17.1 ms, T_H = 0.32 ms,
T_SE/D = 5.6 ms, ...), calibrated for resource-constrained embedded
hardware -- not measured on real hardware in that paper. This report
instead measures **real operation costs on this benchmarking host** (real
AES-256-GCM, real HKDF-SHA256, real SHA-256, via the `cryptography`
bindings to OpenSSL) for the proposed scheme, and separately reports the
**paper's own reference values** for the nine baseline schemes it cites
(full re-implementation of those nine external protocols is a v2 backlog
item, not done here). Both are shown below, never conflated: our numbers
are labeled "measured"; the paper's are labeled "paper-reported" /
"source paper"."""

PAPER_CLAIMED_REDUCTIONS_PCT = {
    "communication": 17.0,
    "processing": 21.0,
    "storage": 12.0,
}


# --- percentage-reduction summary (acceptance criterion 6) ---------------


def _numeric_baseline_values(rows: dict, key_paths: list[str]) -> list[float]:
    """Extract numeric values (skipping non-numeric/None entries like Das
    et al.'s "768+CH*") from a baselines table, excluding the paper's own
    "Proposed Scheme (paper-reported)" row (we compare against *baselines*,
    not against the paper's citation of its own scheme)."""
    values = []
    for name, row in rows.items():
        if name.startswith("Proposed"):
            continue
        v = row
        for key in key_paths:
            v = v.get(key) if isinstance(v, dict) else None
        if isinstance(v, (int, float)):
            values.append(float(v))
    return values


def compute_reduction_summary(results: dict) -> dict:
    baselines = results["baselines"]

    # Communication: our measured session total (bytes) vs baseline total_bits/8.
    # Uses *raw field bytes* (PID + ciphertext + tag + nonce, no envelope),
    # not the JSON+base64 wire size -- the paper's Table IV bit counts are
    # raw bit-packed fields, not a JSON transport encoding, so raw fields
    # is the apples-to-apples comparison. The JSON wire size (which carries
    # ~2x overhead from base64 + field names) is reported separately above
    # and is a demo-transport choice (Section 4.3), not a protocol-inherent
    # cost -- see report text.
    measured_comm_bytes = results["proposed"]["communication"]["session_total_raw_field_bytes"]
    baseline_comm_bytes = [
        v / 8.0 for v in _numeric_baseline_values(baselines["communication_bits_source_paper_table_IV"], ["total_bits"])
    ]
    baseline_comm_mean = sum(baseline_comm_bytes) / len(baseline_comm_bytes)
    comm_pct = (baseline_comm_mean - measured_comm_bytes) / baseline_comm_mean * 100.0

    # Processing: our measured warm device_total + server_handle (ms) vs
    # baseline device+server formula evaluated with Table III constants.
    warm = results["proposed"]["processing"]["warm_steady_state_pairwise_root_cached_FR_3_2"]
    measured_proc_ms = warm["device_total"]["mean_ms"] + warm["server_handle_request"]["mean_ms"]
    baseline_proc_ms = []
    for name, roles in baselines["computation_ms_evaluated_with_table_III_constants"].items():
        if name.startswith("Proposed"):
            continue
        if "device" in roles and "server" in roles:
            baseline_proc_ms.append(roles["device"] + roles["server"])
    baseline_proc_mean = sum(baseline_proc_ms) / len(baseline_proc_ms)
    proc_pct = (baseline_proc_mean - measured_proc_ms) / baseline_proc_mean * 100.0

    # Storage: our measured device+server persisted-state bytes vs baseline device+server bytes.
    storage = results["proposed"]["storage"]
    measured_storage_bytes = storage["device_persisted_state_bytes"] + storage["server_persisted_state_bytes"]
    baseline_storage_bytes = []
    for name, row in baselines["storage_bytes_source_paper_table_VI"].items():
        if name.startswith("Proposed"):
            continue
        s, d = row.get("server_bytes"), row.get("device_bytes")
        if isinstance(s, (int, float)) and isinstance(d, (int, float)):
            baseline_storage_bytes.append(float(s) + float(d))
    baseline_storage_mean = sum(baseline_storage_bytes) / len(baseline_storage_bytes)
    storage_pct = (baseline_storage_mean - measured_storage_bytes) / baseline_storage_mean * 100.0

    def _row(metric: str, measured, baseline_mean, pct: float) -> dict:
        claimed = PAPER_CLAIMED_REDUCTIONS_PCT[metric]
        return {
            "measured": measured,
            "baseline_mean": baseline_mean,
            "measured_reduction_pct_vs_baseline_mean": pct,
            "paper_claimed_reduction_pct": claimed,
            "direction_consistent_with_paper_claim": (pct > 0) == (claimed > 0),
        }

    return {
        "communication": _row("communication", measured_comm_bytes, baseline_comm_mean, comm_pct),
        "processing": _row("processing", measured_proc_ms, baseline_proc_mean, proc_pct),
        "storage": _row("storage", measured_storage_bytes, baseline_storage_mean, storage_pct),
    }


# --- charts (Figures 1-3 equivalents) -------------------------------------


def _chart_communication(results: dict, out_dir: Path) -> Path:
    comm = results["proposed"]["communication"]
    proposed_raw_bytes = comm["session_total_raw_field_bytes"]
    proposed_wire_bytes = comm["session_total_wire_bytes"]
    baselines = results["baselines"]["communication_bits_source_paper_table_IV"]

    names = ["Proposed\n(measured, raw fields)", "Proposed\n(measured, JSON wire)"]
    values = [proposed_raw_bytes, proposed_wire_bytes]
    colors = [_PROPOSED_COLOR, "#7fb3d5"]
    for name, row in baselines.items():
        if name.startswith("Proposed"):
            continue
        names.append(name.replace(" et al.", "\net al."))
        values.append(row["total_bits"] / 8.0)
        colors.append(_BASELINE_COLOR)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(names, values, color=colors)
    ax.set_xlabel("Total per-session communication cost (bytes)")
    ax.set_title(
        "Communication cost -- measured (proposed) vs paper-reported (baselines)\n"
        "(Fig. 2 equivalent; baselines are raw bit-packed fields per Table IV, so \"raw fields\" is the fair comparison)"
    )
    ax.invert_yaxis()
    fig.tight_layout()
    path = out_dir / "communication_cost.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _chart_processing_vs_population(results: dict, out_dir: Path) -> tuple[Path, Path]:
    points = results["proposed"]["processing_vs_device_population"]
    x = [p["num_devices"] for p in points]
    y = [p["mean_ms"] for p in points]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, y, marker="o", color=_PROPOSED_COLOR, label="Proposed (measured: server handle_auth_request)")
    ax.set_xlabel("Number of devices enrolled with the server")
    ax.set_ylabel("Mean processing time (ms)")
    ax.set_title("Processing cost vs. device population\n(Fig. 1 equivalent, paper's \"vehicles\" axis relabeled)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    png_path = out_dir / "processing_cost.png"
    fig.savefig(png_path, dpi=150)
    plt.close(fig)

    csv_path = out_dir / "processing_cost_vs_population.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["num_devices", "n_trials", "mean_ms", "min_ms", "max_ms"])
        writer.writeheader()
        writer.writerows(points)

    return png_path, csv_path


def _chart_storage(results: dict, out_dir: Path) -> Path:
    storage = results["proposed"]["storage"]
    baselines = results["baselines"]["storage_bytes_source_paper_table_VI"]

    names = ["Proposed\n(measured)"]
    server_vals = [storage["server_persisted_state_bytes"]]
    device_vals = [storage["device_persisted_state_bytes"]]
    for name, row in baselines.items():
        if name.startswith("Proposed"):
            continue
        s, d = row.get("server_bytes"), row.get("device_bytes")
        if not isinstance(s, (int, float)) or not isinstance(d, (int, float)):
            continue  # e.g. Das et al.'s "768+CH*" -- not numerically comparable
        names.append(name.replace(" et al.", "\net al."))
        server_vals.append(s)
        device_vals.append(d)

    x = range(len(names))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar([i - width / 2 for i in x], server_vals, width, label="Server storage (bytes)", color=_PROPOSED_COLOR)
    ax.bar([i + width / 2 for i in x], device_vals, width, label="Device storage (bytes)", color=_BASELINE_COLOR)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=30, ha="right")
    ax.set_ylabel("Bytes")
    ax.set_title("Storage cost -- measured (proposed) vs paper-reported (baselines)\n(Fig. 3 equivalent)")
    ax.legend()
    fig.tight_layout()
    path = out_dir / "storage_cost.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# --- rendering --------------------------------------------------------


def _fmt(value, digits: int = 3) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _render_reduction_table_md(summary: dict) -> str:
    lines = [
        "| Metric | Measured | Baseline mean (paper-reported) | Our reduction | Paper claims | Direction matches? |",
        "|---|---|---|---|---|---|",
    ]
    units = {"communication": "bytes", "processing": "ms", "storage": "bytes"}
    for metric, row in summary.items():
        lines.append(
            f"| {metric.capitalize()} | {_fmt(row['measured'])} {units[metric]} | "
            f"{_fmt(row['baseline_mean'])} {units[metric]} | "
            f"{_fmt(row['measured_reduction_pct_vs_baseline_mean'], 1)}% | "
            f"~{row['paper_claimed_reduction_pct']:.0f}% | "
            f"{'Yes' if row['direction_consistent_with_paper_claim'] else 'No'} |"
        )
    return "\n".join(lines)


def render_markdown(results: dict, out_dir: Path) -> str:
    summary = compute_reduction_summary(results)
    comm_png = _chart_communication(results, out_dir)
    proc_pop_png, proc_csv = _chart_processing_vs_population(results, out_dir)
    storage_png = _chart_storage(results, out_dir)

    env = results["environment"]

    md = f"""# Hybrid ECC IoT Authentication -- Benchmark Report

Source paper: Al-Rasheed et al., "A Low-Cost Hybrid Elliptic Curve
Cryptography Authentication Protocol for Trustworthy Internet of Things
Communication," IEEE Trans. Consumer Electronics, vol. 72, no. 2,
pp. 4483-4491, May 2026.

## Environment

- Python: `{env['python_version']}`
- Platform: `{env['platform']}`
- Processor: `{env['processor']}`
- `cryptography` version: `{env['cryptography_version']}`

{METHODOLOGY_NOTE}

## Summary: measured reduction vs. paper's claimed reductions

The paper claims approximately 17% lower communication cost, 21% lower
processing cost, and 12% lower storage cost versus the schemes it compares
against. The table below computes the analogous reduction from this
project's own measurements (proposed scheme) against the mean of the
paper-reported baseline values for the same metric.

{_render_reduction_table_md(summary)}

The communication row compares **raw field bytes** (PID + ciphertext + tag
+ nonce, {results['proposed']['communication']['session_total_raw_field_bytes']} bytes)
against the paper's Table IV bit-packed totals, since that is the
apples-to-apples comparison. Our demo transport's actual JSON+base64 wire
size is larger ({results['proposed']['communication']['session_total_wire_bytes']} bytes) due to
envelope/encoding overhead (protocol/messages.py) that is a transport
choice (Section 4.3), not a property of the cryptographic protocol itself.

*"Direction matches?"* only checks whether our reproduction agrees with
the paper on the *sign* of the effect (lower cost or not) -- it does not
claim to reproduce the exact percentage, since we measure real wall-clock
time on different hardware rather than reusing the paper's assumed Table
III constants (see methodology note above).

## Communication cost (BR-1, Fig. 2 equivalent)

Proposed scheme, measured on real serialized M1/M2 wire messages:

- M1 (device -> server): {results['proposed']['communication']['m1_wire_bytes']} bytes
  (breakdown: {results['proposed']['communication']['m1_field_breakdown_raw_bytes']})
- M2 (server -> device): {results['proposed']['communication']['m2_wire_bytes']} bytes
  (breakdown: {results['proposed']['communication']['m2_field_breakdown_raw_bytes']})
- Session total: {results['proposed']['communication']['session_total_wire_bytes']} bytes
- Offline registration: {results['proposed']['communication']['offline_registration_wire_bytes']} bytes
  -- {results['proposed']['communication']['offline_registration_note']}

![Communication cost]({comm_png.name})

## Processing cost (BR-2, Fig. 1 equivalent)

Warm (steady-state, pairwise root cached per FR-3.2), {results['proposed']['processing']['n_trials']} trials:

- Device (build + complete): mean {_fmt(results['proposed']['processing']['warm_steady_state_pairwise_root_cached_FR_3_2']['device_total']['mean_ms'])} ms,
  p95 {_fmt(results['proposed']['processing']['warm_steady_state_pairwise_root_cached_FR_3_2']['device_total']['p95_ms'])} ms
- Server (handle_auth_request): mean {_fmt(results['proposed']['processing']['warm_steady_state_pairwise_root_cached_FR_3_2']['server_handle_request']['mean_ms'])} ms,
  p95 {_fmt(results['proposed']['processing']['warm_steady_state_pairwise_root_cached_FR_3_2']['server_handle_request']['p95_ms'])} ms

Cold (pairwise root re-derived every session, matching the paper's literal
Eq. 22 per-session KDF cost), {results['proposed']['processing']['cold_pairwise_root_recomputed_every_session_matches_paper_Eq22']['n_trials']} trials:

- Device total: mean {_fmt(results['proposed']['processing']['cold_pairwise_root_recomputed_every_session_matches_paper_Eq22']['device_total']['mean_ms'])} ms
- Server total: mean {_fmt(results['proposed']['processing']['cold_pairwise_root_recomputed_every_session_matches_paper_Eq22']['server_total']['mean_ms'])} ms

![Processing cost vs device population]({proc_pop_png.name})

Underlying data: `{proc_csv.name}`

### Paper-reported baseline computation formulas (Table V), evaluated with Table III constants

| Scheme | User/Client (ms) | Device (ms) | Server (ms) |
|---|---|---|---|
""" + "\n".join(
        f"| {name} | {_fmt(roles.get('user_client', float('nan')))} | {_fmt(roles.get('device', float('nan')))} | {_fmt(roles.get('server', float('nan')))} |"
        for name, roles in results["baselines"]["computation_ms_evaluated_with_table_III_constants"].items()
    ) + f"""

## Storage cost (BR-3, Fig. 3 equivalent)

- Device persisted state: {results['proposed']['storage']['device_persisted_state_bytes']} bytes
  (breakdown: {results['proposed']['storage']['device_state_breakdown_bytes']})
- Server persisted state: {results['proposed']['storage']['server_persisted_state_bytes']} bytes
  (breakdown: {results['proposed']['storage']['server_state_breakdown_bytes']})

![Storage cost]({storage_png.name})

## Raw data

Full machine-readable results: `results.json`
"""
    return md


_HTML_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Hybrid ECC IoT Auth -- Benchmark Report</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; color: #1a1a1a; }}
h1, h2, h3 {{ color: #14344f; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }}
th {{ background: #f0f4f8; }}
img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; margin: 0.5rem 0; }}
.callout {{ background: #eef4fa; border-left: 4px solid {color}; padding: 0.75rem 1rem; margin: 1rem 0; }}
code {{ background: #f0f0f0; padding: 0.1rem 0.3rem; border-radius: 3px; }}
</style></head><body>
{body}
</body></html>
""".replace("{color}", _PROPOSED_COLOR)


def _markdown_table_to_html(md_table: str) -> str:
    rows = [line for line in md_table.strip().splitlines() if line.strip()]
    header_cells = [c.strip() for c in rows[0].strip("|").split("|")]
    body_rows = [
        [c.strip() for c in row.strip("|").split("|")]
        for row in rows[2:]  # skip header + separator
    ]
    html = ["<table>", "<tr>" + "".join(f"<th>{c}</th>" for c in header_cells) + "</tr>"]
    for row in body_rows:
        html.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    html.append("</table>")
    return "\n".join(html)


def render_html(results: dict, out_dir: Path) -> str:
    """Self-contained: charts are embedded as base64 PNGs, not linked."""
    summary = compute_reduction_summary(results)

    def _b64_img(path: Path) -> str:
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'<img src="data:image/png;base64,{data}" alt="{path.stem}">'

    comm_png = out_dir / "communication_cost.png"
    proc_png = out_dir / "processing_cost.png"
    storage_png = out_dir / "storage_cost.png"

    env = results["environment"]
    reduction_table_html = _markdown_table_to_html(_render_reduction_table_md(summary))

    body = f"""
<h1>Hybrid ECC IoT Authentication &mdash; Benchmark Report</h1>
<p>Source paper: Al-Rasheed et al., &ldquo;A Low-Cost Hybrid Elliptic Curve
Cryptography Authentication Protocol for Trustworthy Internet of Things
Communication,&rdquo; <em>IEEE Trans. Consumer Electronics</em>, vol. 72,
no. 2, pp. 4483&ndash;4491, May 2026.</p>

<h2>Environment</h2>
<ul>
<li>Python: <code>{env['python_version']}</code></li>
<li>Platform: <code>{env['platform']}</code></li>
<li>Processor: <code>{env['processor']}</code></li>
<li><code>cryptography</code> version: <code>{env['cryptography_version']}</code></li>
</ul>

<div class="callout"><p>{METHODOLOGY_NOTE.replace(chr(10), ' ')}</p></div>

<h2>Summary: measured reduction vs. paper's claimed reductions</h2>
{reduction_table_html}

<h2>Communication cost (Fig. 2 equivalent)</h2>
{_b64_img(comm_png)}

<h2>Processing cost vs. device population (Fig. 1 equivalent)</h2>
{_b64_img(proc_png)}

<h2>Storage cost (Fig. 3 equivalent)</h2>
{_b64_img(storage_png)}

<h2>Raw data</h2>
<p>Full machine-readable results are written alongside this report as <code>results.json</code>.</p>
"""
    return _HTML_TEMPLATE.format(body=body)


def generate_report(results: dict, out_dir: str | Path) -> dict:
    """BR-4.1: writes report.md, report.html, results.json, and the chart
    PNGs/CSV into `out_dir`. Returns the paths written."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    md = render_markdown(results, out_path)  # also generates the PNGs/CSV as a side effect
    (out_path / "report.md").write_text(md, encoding="utf-8")

    html = render_html(results, out_path)
    (out_path / "report.html").write_text(html, encoding="utf-8")

    (out_path / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    return {
        "report_md": out_path / "report.md",
        "report_html": out_path / "report.html",
        "results_json": out_path / "results.json",
        "communication_png": out_path / "communication_cost.png",
        "processing_png": out_path / "processing_cost.png",
        "processing_csv": out_path / "processing_cost_vs_population.csv",
        "storage_png": out_path / "storage_cost.png",
    }
