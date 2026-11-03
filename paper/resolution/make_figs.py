#!/usr/bin/env python3
"""Figures and the ranked complexity table for the pseudonym-resolution paper (both versions).
Every number is read from a repository file:
  research/pseudonym_resolution/measured.csv     implementation probe counts and state (resolution_costs.py)
  research/pseudonym_resolution/cost_model.csv   per-n cost model fed to OMNeT++
  research/pseudonym_resolution/sim/results.csv  OMNeT++ 6.4 runs, BASE Table II environment, Table III constants
The N = 1 column of the table is the base paper's own value (Table V x Table III; Table VI), not ours.
Run from the repository root: .venv/bin/python -I paper/resolution/make_figs.py
"""
import csv
import collections
import json
import statistics as st
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "figs"
OUT.mkdir(exist_ok=True)
RES = ROOT / "research/pseudonym_resolution"

PAPER_SESSION_MS = 2 * (2 * 0.32 + 2 * 5.6)   # Table V x Table III, device + server = 23.68 ms
PAPER_SERVER_BITS = 320                         # Table VI, server storage
T_H = 0.32

# name, short label, origin, time O(), space O(), colour, marker
S = {
    "O2": ("Counter + precomputed table", "O2", "ours", r"$O(1)$", r"$O(NF)$"),
    "O4": ("Clock + per-epoch table", "O4", r"\cite{tsudik}", r"$O(1)$, $+O(N)$/epoch", r"$O(NW_t)$"),
    "MW": ("Key tree", "MW", r"\cite{molnar}", r"$O(\delta\log_\delta N)$", r"$O(N)$"),
    "CR": ("Randomized hash lock", "CR", r"\cite{weis}", r"$O(N)$", r"$O(N)$"),
    "O3": ("Clock + linear scan", "O3", "ours", r"$O(NW_t)$", r"$O(N)$"),
    "TM": ("Rainbow time-memory trade-off", "TM", r"\cite{avoine05,ado05}", r"$O((Nm)^{2/3})$", r"$O((Nm)^{2/3})$"),
    "O1": ("Counter + linear scan", "O1", r"\cite{ohkubo}", r"$O(NW)$", r"$O(N)$"),
}
COL = {"O1": "#D55E00", "O2": "#0072B2", "O3": "#E69F00", "O4": "#56B4E9", "TM": "#CC79A7", "CR": "#009E73", "MW": "#555555"}
MK = {"O1": "o", "O2": "s", "O3": "^", "O4": "v", "TM": "D", "CR": "P", "MW": "X"}
plt.rcParams.update({"font.size": 7.5, "font.family": "serif", "axes.edgecolor": "#555", "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e6e6e6",
                     "grid.linewidth": 0.5, "axes.axisbelow": True, "legend.frameon": False, "pdf.fonttype": 42})

measured = list(csv.DictReader(open(RES / "measured.csv")))
sim = list(csv.DictReader(open(RES / "sim/results.csv")))
g = collections.defaultdict(list)
for r in sim:
    g[(r["config"], int(r["N"]))].append(r)
NS = sorted({int(r["N"]) for r in sim})


def lat(cfg, n):
    v = [float(r["latency_mean_ms"]) for r in g[(cfg, n)] if float(r["sessions_completed"] or 0) > 0]
    return st.mean(v), min(v), max(v)


def store_kb(s, n):
    """Mean per-server storage in the simulated deployment: Table VI's 320 bits per enrolled device plus resolution state."""
    v = [float(r["mean_enrolled_per_server"]) * PAPER_SERVER_BITS / 8 + float(r["mean_state_bytes_per_server"])
         for r in g[(f"R_{s}", n)]]
    return st.mean(v) / 1024


def meas(s, key):
    rows = sorted((int(r["n"]), float(r[key])) for r in measured if r["strategy"] == s)
    return [a for a, _ in rows], [b for _, b in rows]


# ---- ranked table --------------------------------------------------------------------------------------------
TN = [10, 100, 500, 1000]
order = sorted(S, key=lambda s: lat(f"R_{s}", 1000)[0])
summary = {"paper_session_ms": PAPER_SESSION_MS, "paper_server_bits": PAPER_SERVER_BITS, "order": order, "rows": {}}


def fmt_ms(x):
    return f"{x:,.0f}" if x >= 1000 else (f"{x:.1f}" if x >= 100 else f"{x:.2f}")


def fmt_kb(x):
    return f"{x:.1f}" if x >= 10 else f"{x:.2f}"


lines = []
for rank, s in enumerate(order, 1):
    name, short, origin, to, so = S[s]
    t = [lat(f"R_{s}", n)[0] for n in TN]
    m = [store_kb(s, n) for n in TN]
    summary["rows"][s] = {"latency_ms": dict(zip(TN, t)), "storage_kb": dict(zip(TN, m)),
                          "latency_noadv_ms": {n: lat(f"H_{s}", n)[0] for n in TN}}
    origin_tex = origin if origin != "ours" else "ours"
    lines.append(f"{rank} & {short} & {name} {origin_tex if origin_tex != 'ours' else ''} & {to} & {so} & "
                 f"{PAPER_SESSION_MS:.2f} & " + " & ".join(fmt_ms(x) for x in t) + f" & {PAPER_SERVER_BITS/8/1024:.2f} & "
                 + " & ".join(fmt_kb(x) for x in m) + r" \\")
(OUT / "table_ranked.tex").write_text("\\def\\rankedrows{%\n" + "\n".join(lines) + "\n}\n")
summary["none_latency_ms"] = {n: lat("R_none", n)[0] for n in NS}
summary["mean_enrolled"] = {n: st.mean(float(r["mean_enrolled_per_server"]) for r in g[("R_O1", n)]) for n in NS}
summary["n_servers"] = {n: st.mean(float(r["n_servers"]) for r in g[("R_O1", n)]) for n in NS}
summary["max_seed_spread_1000"] = {s: lat(f"R_{s}", 1000)[2] - lat(f"R_{s}", 1000)[1] for s in S}
for s in S:
    ns, h = meas(s, "honest_mean")
    _, f = meas(s, "forged")
    _, b = meas(s, "state_bytes")
    summary["rows"][s]["single_server"] = {n: {"honest": hh, "forged": ff, "state_bytes": bb} for n, hh, ff, bb in zip(ns, h, f, b)}
json.dump(summary, open(OUT / "summary.json", "w"), indent=1)

# ---- Fig.: probes per authentication against N (single server, implementation counts) ------------------------
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.35))
for s in order:
    ns, h = meas(s, "honest_mean")
    _, f = meas(s, "forged")
    k = [(n, x) for n, x in zip(ns, h) if x > 0]
    if k:
        axs[0].plot(*zip(*k), marker=MK[s], ms=3, lw=1, color=COL[s], label=S[s][1])
    k = [(n, x) for n, x in zip(ns, f) if x > 0]
    if k:
        axs[1].plot(*zip(*k), marker=MK[s], ms=3, lw=1, color=COL[s], label=S[s][1])
for ax, t in zip(axs, ("(a) Honest authentication", "(b) Forged pseudonym")):
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("Devices enrolled at the server, $N$")
    ax.set_title(t, fontsize=7.5)
axs[0].set_ylabel("H2 probes (mean)")
axs[1].text(0.97, 0.05, "O2, O4: 0 probes (table miss)", transform=axs[1].transAxes, ha="right", fontsize=6.5, color="#444")
axs[0].text(0.97, 0.05, "O4: 0 probes per auth.", transform=axs[0].transAxes, ha="right", fontsize=6.5, color="#444")
axs[0].legend(ncol=2, fontsize=6.2, loc="upper left")
axs[1].text(0.03, 0.93, "MW: children of the root only", transform=axs[1].transAxes, fontsize=6.3, color="#444")
fig.tight_layout(); fig.savefig(OUT / "fig_probes.pdf"); plt.close(fig)

# ---- Fig.: simulated latency against N, with and without adversaries -----------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.4), sharey=True)
for ax, pre, t in ((axs[0], "H_", "(a) No adversaries"), (axs[1], "R_", "(b) 5% adversaries, 1 forged M1/s each")):
    m = [lat(f"{pre}none", n)[0] for n in NS]
    ax.plot(NS, m, color="#999", lw=1.2, ls=":", label="Table V only")
    for s in order:
        v = [lat(f"{pre}{s}", n) for n in NS]
        ax.plot(NS, [x[0] for x in v], marker=MK[s], ms=2.6, lw=1, color=COL[s], label=S[s][1])
        ax.fill_between(NS, [x[1] for x in v], [x[2] for x in v], color=COL[s], alpha=0.12, lw=0)
    ax.axhline(PAPER_SESSION_MS, color="#222", lw=0.6, ls="--")
    ax.set_yscale("log"); ax.set_xlabel("Devices in the network, $N$"); ax.set_title(t, fontsize=7.5)
axs[0].set_ylabel("Mean session latency (ms)")
axs[0].text(5, PAPER_SESSION_MS * 0.72, "base paper, 23.68 ms (N = 1)", ha="left", fontsize=6.3)
axs[1].legend(ncol=1, fontsize=6.5, loc="upper left", bbox_to_anchor=(1.0, 1.0))
fig.tight_layout(); fig.savefig(OUT / "fig_latency.pdf"); plt.close(fig)

# ---- Fig.: storage against N, and the time-memory plane at N = 1000 --------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.35))
for s in order:
    ns, b = meas(s, "state_bytes")
    tot = [(n, (n * PAPER_SERVER_BITS / 8 + x) / 1024) for n, x in zip(ns, b)]
    axs[0].plot(*zip(*tot), marker=MK[s], ms=3, lw=1, color=COL[s], label=S[s][1])
ns = [n for n, _ in tot]
axs[0].plot(ns, [n * PAPER_SERVER_BITS / 8 / 1024 for n in ns], color="#222", lw=0.7, ls="--", label="Table VI only")
axs[0].set_xscale("log"); axs[0].set_yscale("log")
axs[0].set_xlabel("Devices enrolled at the server, $N$"); axs[0].set_ylabel("Server storage (KB)")
axs[0].set_title("(a) Storage, one server", fontsize=7.5)
for s in order:
    row = {int(r["n"]): r for r in measured if r["strategy"] == s}[1000]
    x = (1000 * PAPER_SERVER_BITS / 8 + float(row["state_bytes"])) / 1024
    y = max(float(row["honest_mean"]), 0.5) * T_H
    axs[1].scatter(x, y, color=COL[s], marker=MK[s], s=22, zorder=3)
    axs[1].annotate(S[s][1], (x, y), textcoords="offset points", xytext=(4, 3), fontsize=6.5)
axs[1].set_xscale("log"); axs[1].set_yscale("log")
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter
axs[1].xaxis.set_major_locator(FixedLocator([40, 60, 100, 200, 400])); axs[1].xaxis.set_minor_locator(NullLocator())
axs[1].xaxis.set_major_formatter(ScalarFormatter()); axs[1].set_xlim(33, 480)
axs[1].set_xlabel("Server storage at $N=1000$ (KB)"); axs[1].set_ylabel("Resolution time per auth. (ms)")
axs[1].set_title(r"(b) Time against memory, $N=1000$, $T_H=0.32$ ms", fontsize=7.5)
axs[1].text(0.03, 0.04, "O4 plotted at 0.5 probe (it needs 0)", transform=axs[1].transAxes, fontsize=6, color="#444")
axs[0].legend(ncol=2, fontsize=6.2, loc="upper left")
fig.tight_layout(); fig.savefig(OUT / "fig_storage.pdf"); plt.close(fig)

print("order:", order)
for s in order:
    print(s, {n: round(v, 2) for n, v in summary["rows"][s]["latency_ms"].items()},
          {n: round(v, 2) for n, v in summary["rows"][s]["storage_kb"].items()})
print("Table V only:", {n: round(v, 2) for n, v in summary["none_latency_ms"].items()})
