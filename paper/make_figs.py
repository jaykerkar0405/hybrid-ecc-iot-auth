#!/usr/bin/env python3
# Copyright (c) 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur
# SPDX-License-Identifier: Apache-2.0
"""Figures and the ranked complexity table for the pseudonym-resolution paper (both versions).
Every number is read from a repository file:
  evaluation/resolution/measured.csv     implementation probe counts and state (resolution_costs.py)
  evaluation/resolution/cost_model.csv   per-n cost model fed to OMNeT++
  evaluation/resolution/sim/results.csv  OMNeT++ 6.4 runs, BASE Table II environment, Table III constants
The N = 1 column of the table is the base paper's own value (Table V x Table III; Table VI), not ours.
Run from the repository root: python -I paper/make_figs.py
"""
import csv
import collections
import json
import statistics as st
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
import argparse  # noqa: E402

_ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
_ap.add_argument("--width", type=float, default=516 / 72.27,
                 help="figure width in inches; default is the IEEEtran conference \\textwidth (516 pt), so figures are not scaled")
_ap.add_argument("--hscale", type=float, default=0.9, help="scale factor for the figure heights (the width is --width)")
_ap.add_argument("--stack", action="store_true", help="stack the two panels of each figure vertically (narrow, single-column layouts)")
_ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "figs", help="output directory")
ARGS = _ap.parse_args()
OUT = ARGS.out
OUT.mkdir(exist_ok=True)
RES = ROOT / "evaluation/resolution"

PAPER_SESSION_MS = 2 * (2 * 0.32 + 2 * 5.6)   # Table V x Table III, device + server = 23.68 ms
PAPER_SERVER_BITS = 320                         # Table VI, server storage
T_H = 0.32

# name, short label, origin, time O(), space O(), colour, marker
S = {
    "O2": ("Counter + precomputed table", "O2", "ours", r"$O(1)$", r"$O(nF)$"),
    "O4": ("Clock + per-epoch table", "O4", r"\cite{tsudik}", r"$O(1)$, $+O(n)$ per epoch", r"$O(nW_{\mathrm{c}})$"),
    "MW": ("Key tree", "MW", r"\cite{molnar}", r"$O(\delta\log_\delta n)$", r"$O(n)$"),
    "CR": ("Randomised hash lock", "CR", r"\cite{weis}", r"$O(n)$", r"$O(n)$"),
    "O3": ("Clock + linear scan", "O3", "ours", r"$O(nW_{\mathrm{c}})$", r"$O(n)$"),
    "TM": ("Rainbow time-memory trade-off", "TM", r"\cite{avoine05,ado05}", r"$O((nm)^{2/3})$", r"$O((nm)^{2/3})$"),
    "O1": ("Counter + linear scan", "O1", r"\cite{ohkubo}", r"$O(nW)$", r"$O(n)$"),
}
COL = {"O1": "#D55E00", "O2": "#0072B2", "O3": "#E69F00", "O4": "#56B4E9", "TM": "#CC79A7", "CR": "#009E73", "MW": "#555555"}
LS = {"O1": "-", "O2": "--", "O3": "-.", "O4": (0, (1, 1.2)), "TM": "-", "CR": "--", "MW": "-."}   # with the markers, tells the curves apart in greyscale
MK = {"O1": "o", "O2": "s", "O3": "^", "O4": "v", "TM": "D", "CR": "P", "MW": "X"}
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["STIXGeneral", "Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "mathtext.fontset": "stix", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.edgecolor": "#444", "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e4e4e4", "grid.linewidth": 0.5, "axes.axisbelow": True,
    "xtick.direction": "out", "ytick.direction": "out", "xtick.major.size": 3, "ytick.major.size": 3,
    "xtick.minor.size": 1.6, "ytick.minor.size": 1.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.minor.width": 0.4, "ytick.minor.width": 0.4, "legend.frameon": False, "lines.solid_capstyle": "round",
    "pdf.fonttype": 42, "savefig.pad_inches": 0.02,
})
STACK = ARGS.stack
NARROW = ARGS.width < 5.5      # single-column venues: two-row legends, wider left margin
FIG_W = ARGS.width   # inches; figures are included at \textwidth, so no scaling
LW, MS = 1.15, 3.2
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402


def plain(x, _):
    return f"{x:,.0f}" if x >= 1 else f"{x:g}"


def style_log(ax, which="y"):
    """Plain decimal tick labels (1, 10, 100, 1,000) with unlabeled minor ticks."""
    axis = ax.yaxis if which == "y" else ax.xaxis
    axis.set_major_locator(LogLocator(base=10, numticks=12))
    axis.set_minor_locator(LogLocator(base=10, subs=range(2, 10), numticks=12))
    axis.set_major_formatter(FuncFormatter(plain))
    axis.set_minor_formatter(NullFormatter())


def panel_title(ax, text):
    ax.set_title(text, loc="left", fontsize=8.5, fontweight="bold", pad=4)


def top_legend(fig, handles, ncol):
    fig.legend(handles=handles, loc="upper center", ncol=ncol, bbox_to_anchor=(0.5, 1.0), frameon=False,
               handlelength=1.8, columnspacing=1.3, handletextpad=0.5, borderaxespad=0.0)


def make_axes(h, gridspec, **kw):
    """Two panels side by side (default) or stacked (--stack, each panel about 2 in high)."""
    if STACK:
        fig, axs = plt.subplots(2, 1, figsize=(FIG_W, 2 * 1.7 + 0.95), **kw)
        return fig, axs
    return plt.subplots(1, 2, figsize=(FIG_W, h * ARGS.hscale), gridspec_kw=gridspec, **kw)


def adjust(fig, **side):
    """subplots_adjust for the side-by-side layout, or fixed margins for the stacked one."""
    if STACK:
        fig.subplots_adjust(top=0.86, bottom=0.085, left=0.15, right=0.97, hspace=0.5)
    elif NARROW:
        fig.subplots_adjust(top=side.get("top_narrow", 0.77), bottom=0.16, left=0.125, right=0.985, wspace=side.get("wspace_narrow", 0.3))
    else:
        side.pop("wspace_narrow", None)
        side.pop("top_narrow", None)
        fig.subplots_adjust(**side)


def strategy_handles(order):
    return [Line2D([0], [0], color=COL[s], marker=MK[s], ms=MS, lw=LW, ls=LS[s], label=S[s][1]) for s in order]


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
    """Mean per-server storage in the simulated deployment: Table VI of [1], 320 bits per enrolled device plus resolution state."""
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
comp, latr, stor, both = [], [], [], []
for rank, s_ in enumerate(order, 1):
    name, short, origin, to, so = S[s_]
    tt = [lat(f"R_{s_}", n)[0] for n in TN]
    mm = [store_kb(s_, n) for n in TN]
    comp.append(f"{rank} & {short} {name} {origin if origin != 'ours' else ''} & {to} & {so} \\\\")
    latr.append(f"{rank} & {short} & {PAPER_SESSION_MS:.2f} & " + " & ".join(fmt_ms(x) for x in tt) + r" \\")
    stor.append(f"{rank} & {short} & {PAPER_SERVER_BITS/8/1024:.2f} & " + " & ".join(fmt_kb(x) for x in mm) + r" \\")
    both.append(f"{rank} & {short} & {PAPER_SESSION_MS:.2f} & " + " & ".join(fmt_ms(x) for x in tt) + f" & {PAPER_SERVER_BITS/8/1024:.2f} & "
                + " & ".join(fmt_kb(x) for x in mm) + r" \\")
(OUT / "table_ranked.tex").write_text("\\def\\rankedrows{%\n" + "\n".join(lines) + "\n}\n"
    + "\\def\\rankedcomprows{%\n" + "\n".join(comp) + "\n}\n"      # narrow layouts: complexity block
    + "\\def\\rankedlatrows{%\n" + "\n".join(latr) + "\n}\n"       # latency block
    + "\\def\\rankedstorrows{%\n" + "\n".join(stor) + "\n}\n"       # storage block
    + "\\def\\rankedlsrows{%\n" + "\n".join(both) + "\n}\n")     # latency and storage side by side, no complexity
summary["none_latency_ms"] = {n: lat("R_none", n)[0] for n in NS}
summary["mean_enrolled"] = {n: st.mean(float(r["mean_enrolled_per_server"]) for r in g[("R_O1", n)]) for n in NS}
summary["n_servers"] = {n: st.mean(float(r["n_servers"]) for r in g[("R_O1", n)]) for n in NS}
summary["max_seed_spread_1000"] = {s: lat(f"R_{s}", 1000)[2] - lat(f"R_{s}", 1000)[1] for s in S}
for s in S:
    ns, h = meas(s, "honest_mean")
    _, f = meas(s, "forged")
    _, b = meas(s, "state_bytes")
    summary["rows"][s]["single_server"] = {n: {"honest": hh, "forged": ff, "state_bytes": bb} for n, hh, ff, bb in zip(ns, h, f, b)}
# one server enrolling 1,000 devices (Fig. 4): resolution state alone, and with the base paper's 40 bytes per device; KiB = 1,024 B
summary["single_server_n1000_kb"] = {s: {"resolution_state": summary["rows"][s]["single_server"][1000]["state_bytes"] / 1024,
                                         "total_with_base_storage": (1000 * PAPER_SERVER_BITS / 8 + summary["rows"][s]["single_server"][1000]["state_bytes"]) / 1024}
                                     for s in S}
json.dump(summary, open(OUT / "summary.json", "w"), indent=1)

# ---- Fig.: probes per authentication against N (single server, implementation counts) ------------------------
fig, axs = make_axes(2.75, {"wspace": 0.22})
for s in order:
    ns, h = meas(s, "honest_mean")
    _, f = meas(s, "forged")
    for ax, ys in ((axs[0], h), (axs[1], f)):
        k = [(n, x) for n, x in zip(ns, ys) if x > 0]
        if k:
            ax.plot(*zip(*k), marker=MK[s], ms=MS, lw=LW, ls=LS[s], color=COL[s], clip_on=False)
for ax, t in zip(axs, ("(a) Honest authentication", "(b) Forged pseudonym")):
    ax.set_xscale("log"); ax.set_yscale("log"); style_log(ax, "x"); style_log(ax, "y")
    ax.set_xlabel("Devices enrolled at the server, $n$"); panel_title(ax, t)
    ax.set_xlim(0.8, 1.25e4)
axs[0].set_ylabel("$H_2$ probes per message (mean)")
axs[0].set_ylim(0.25, 3e5); axs[1].set_ylim(0.25, 3e5)
note = dict(fontsize=8, color="#444", style="italic", ha="right")
axs[0].text(0.98, 0.025, "O4 needs 0 probes", transform=axs[0].transAxes, **note)
axs[1].text(0.98, 0.025, "O2, O4: 0 probes (table miss)", transform=axs[1].transAxes, **note)
axs[1].annotate("MW: children of\nthe root only", xy=(1000, 34), xytext=(2600, 95), fontsize=8, color=COL["MW"],
                style="italic", ha="center", va="center", linespacing=1.0,
                arrowprops=dict(arrowstyle="-", color=COL["MW"], lw=0.6, shrinkA=1, shrinkB=2))
top_legend(fig, strategy_handles(order), 4 if (STACK or NARROW) else len(order))
adjust(fig, top=0.82, bottom=0.17, left=0.085, right=0.985, wspace_narrow=0.45)
fig.savefig(OUT / "fig_probes.pdf"); plt.close(fig)

# ---- Fig.: simulated latency against N, with and without adversaries -----------------------------------------
fig, axs = make_axes(2.85, {"wspace": 0.06}, sharey=True)
for ax, pre, t in ((axs[0], "H_", "(a) No adversaries"), (axs[1], "R_", "(b) 5% adversaries, 1 forged $M_1$/s each")):
    m = [lat(f"{pre}none", n)[0] for n in NS]
    ax.plot(NS, m, color="#8a8a8a", lw=1.4, ls=(0, (1, 3)), zorder=2)
    for s in reversed(order):
        v = [lat(f"{pre}{s}", n) for n in NS]
        ax.fill_between(NS, [x[1] for x in v], [x[2] for x in v], color=COL[s], alpha=0.13, lw=0, zorder=1)
        ax.plot(NS, [x[0] for x in v], marker=MK[s], ms=MS - 0.4, lw=LW, ls=LS[s], color=COL[s], zorder=3, clip_on=False)
    ax.axhline(PAPER_SESSION_MS, color="#222", lw=0.7, ls=(0, (4, 2)), zorder=2)
    ax.set_yscale("log"); style_log(ax, "y")
    ax.set_xlim(-25, 1025); ax.set_xticks(range(0, 1001, 200))
    ax.set_xlabel("Devices in the network, $N$"); panel_title(ax, t)
axs[0].set_ylim(18, 1e5)
axs[0].set_ylabel("Mean session latency (ms)")
handles = strategy_handles(order) + [
    Line2D([0], [0], color="#8a8a8a", lw=1.4, ls=(0, (1, 3)), label="Base cost model [1], no resolution"),
    Line2D([0], [0], color="#222", lw=0.7, ls=(0, (4, 2)), label="Base paper [1], 23.68 ms"),
    Patch(facecolor="#777", alpha=0.25, lw=0, label="Min–max over five seeds")]
if STACK or NARROW:
    top_legend(fig, handles, 4)
    if STACK:
        axs[1].set_ylabel("Mean session latency (ms)")
else:
    top_legend(fig, handles[:len(order)], len(order))
    fig.legend(handles=handles[len(order):], loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.915), frameon=False,
               handlelength=1.8, columnspacing=1.6, handletextpad=0.5, borderaxespad=0.0)
adjust(fig, top=0.775, bottom=0.18, left=0.085, right=0.985, wspace_narrow=0.06, top_narrow=0.72)
fig.savefig(OUT / "fig_latency.pdf"); plt.close(fig)

# ---- Fig.: storage against N, and the time-memory plane at N = 1000 --------------------------------------------
fig, axs = make_axes(2.85, {"wspace": 0.24})
for s in order:
    ns, b = meas(s, "state_bytes")
    tot = [(n, (n * PAPER_SERVER_BITS / 8 + x) / 1024) for n, x in zip(ns, b)]
    axs[0].plot(*zip(*tot), marker=MK[s], ms=MS, lw=LW, ls=LS[s], color=COL[s])
ns = [n for n, _ in tot]
axs[0].plot(ns, [n * PAPER_SERVER_BITS / 8 / 1024 for n in ns], color="#222", lw=0.8, ls=(0, (4, 2)))
axs[0].set_xscale("log"); axs[0].set_yscale("log"); style_log(axs[0], "x"); style_log(axs[0], "y")
axs[0].set_xlabel("Devices enrolled at the server, $n$"); axs[0].set_ylabel("Server storage (KiB)")
panel_title(axs[0], "(a) Storage at one server")
offs = {"O2": (-4, 7), "O4": (-6, 6), "MW": (6, -9), "CR": (6, -3), "O3": (6, 4), "TM": (6, 3), "O1": (7, -3)}
for s in order:
    row = {int(r["n"]): r for r in measured if r["strategy"] == s}[1000]
    x = (1000 * PAPER_SERVER_BITS / 8 + float(row["state_bytes"])) / 1024
    y = max(float(row["honest_mean"]), 0.5) * T_H
    axs[1].scatter(x, y, color=COL[s], marker=MK[s], s=26, zorder=3)
    axs[1].annotate(S[s][1], (x, y), textcoords="offset points", xytext=offs.get(s, (5, 3)), fontsize=8,
                    color=COL[s] if s != "O4" else "#2d7fb5")
axs[1].set_xscale("log"); axs[1].set_yscale("log")
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter  # noqa: E402
axs[1].xaxis.set_major_locator(FixedLocator([40, 60, 100, 200, 400])); axs[1].xaxis.set_minor_locator(NullLocator())
axs[1].xaxis.set_major_formatter(ScalarFormatter()); axs[1].set_xlim(33, 480)
style_log(axs[1], "y"); axs[1].set_ylim(0.1, 2.5e4)
axs[1].set_xlabel("Server storage at $n = 1{,}000$ (KiB)"); axs[1].set_ylabel("Resolution time per auth. (ms)")
panel_title(axs[1], "(b) Time against memory, $n = 1{,}000$")
axs[1].text(0.02, 0.05, "O4 plotted at 0.5 probe (needs 0)", transform=axs[1].transAxes, fontsize=8,
            color="#444", style="italic", ha="left")
top_legend(fig, strategy_handles(order) + [Line2D([0], [0], color="#222", lw=0.8, ls=(0, (4, 2)),
                                                    label="Base storage [1] only")], 4 if (STACK or NARROW) else len(order) + 1)
adjust(fig, top=0.82, bottom=0.17, left=0.085, right=0.985, wspace_narrow=0.42)
fig.savefig(OUT / "fig_storage.pdf"); plt.close(fig)

print("order:", order)
for s in order:
    print(s, {n: round(v, 2) for n, v in summary["rows"][s]["latency_ms"].items()},
          {n: round(v, 2) for n, v in summary["rows"][s]["storage_kb"].items()})
print("No-resolution baseline:", {n: round(v, 2) for n, v in summary["none_latency_ms"].items()})
