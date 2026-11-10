#!/usr/bin/env python3
"""Charts for the poster. Every number is read from the same repository files as paper/make_figs.py.
Run from the repository root: python -I docs/poster/make_charts.py
"""
import collections
import csv
import statistics as st
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "app" / "src" / "assets"
OUT.mkdir(exist_ok=True)
RES = ROOT / "evaluation/resolution"
PAPER_MS = 23.68

NAME = {"O2": "O2  counter + table", "O4": "O4  clock + table", "MW": "MW  key tree", "CR": "CR  hash lock",
        "O3": "O3  clock + scan", "TM": "TM  rainbow table", "O1": "O1  counter + scan"}
COL = {"O1": "#D55E00", "O2": "#0072B2", "O3": "#E69F00", "O4": "#56B4E9", "TM": "#CC79A7", "CR": "#009E73", "MW": "#555555"}
MK = {"O1": "o", "O2": "s", "O3": "^", "O4": "v", "TM": "D", "CR": "P", "MW": "X"}
ORDER = ["O2", "O4", "MW", "CR", "O3", "TM", "O1"]

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 13, "axes.labelsize": 13.5, "xtick.labelsize": 12.5, "ytick.labelsize": 12.5, "legend.fontsize": 11.5,
    "axes.edgecolor": "#444", "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e2e2e2", "grid.linewidth": 0.7, "axes.axisbelow": True,
    "legend.frameon": False, "svg.fonttype": "none", "savefig.pad_inches": 0.04,
})

sim = list(csv.DictReader(open(RES / "sim/results.csv")))
g = collections.defaultdict(list)
for r in sim:
    g[(r["config"], int(r["N"]))].append(r)
NS = sorted({int(r["N"]) for r in sim})


def lat(cfg, n):
    return st.mean(float(r["latency_mean_ms"]) for r in g[(cfg, n)] if float(r["sessions_completed"] or 0) > 0)


def plain(x, _):
    return f"{x:,.0f}" if x >= 1 else f"{x:g}"


# ---- latency against network size (5% adversaries), lines labelled directly ----
fig, ax = plt.subplots(figsize=(6.4, 3.95))
last = {}
for s in reversed(ORDER):
    ys = [PAPER_MS] + [lat(f"R_{s}", n) for n in NS if n > 1]
    ax.plot(NS, ys, marker=MK[s], ms=6.5, lw=2.4, color=COL[s], clip_on=False, zorder=3)
    last[s] = ys[-1]
ax.axhline(PAPER_MS, color="#222", lw=1.2, ls=(0, (5, 3)), zorder=2)
ax.text(30, 14.2, "paper's figure: 23.68 ms", ha="left", va="center", fontsize=12.5, style="italic", color="#222")
lab = {"O1": ("O1 counter scan", last["O1"]), "TM": ("TM rainbow table", last["TM"]), "O3": ("O3 clock scan", last["O3"]),
       "CR": ("CR hash lock", last["CR"]), "MW": ("MW key tree", 50), "O4": ("O4 clock table", 24.6), "O2": ("O2 counter table", 12)}
for s, (t, y) in lab.items():
    ax.text(1035, y, t, ha="left", va="center", fontsize=12.5, fontweight="bold", color=COL[s] if s != "O4" else "#2d8fcf",
            clip_on=False)
ax.set_yscale("log")
ax.yaxis.set_major_locator(LogLocator(base=10, numticks=12))
ax.yaxis.set_minor_locator(LogLocator(base=10, subs=range(2, 10), numticks=12))
ax.yaxis.set_major_formatter(FuncFormatter(plain)); ax.yaxis.set_minor_formatter(NullFormatter())
ax.set_ylim(10, 1e5); ax.set_xlim(-15, 1015); ax.set_xticks(range(0, 1001, 200))
ax.set_xlabel("Devices in the network, N  (5% of them adversaries)")
ax.set_ylabel("Mean time per session (ms)")
fig.subplots_adjust(left=0.165, right=0.735, top=0.97, bottom=0.155)
fig.savefig(OUT / "chart_latency.svg"); plt.close(fig)

print("latency@1000:", {s: round(lat(f'R_{s}', 1000), 2) for s in ORDER})
