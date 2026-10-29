#!/usr/bin/env python3
"""Layer B comparison: OMNeT++ output vs BASE Tables IV/V (paper_tables.py) and the paper's cost model (Table V x Table III)."""
import csv, statistics as st, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "paper_audit"))
from paper_tables import T3, T4, T5
HERE = Path(__file__).resolve().parent
def load(p): return list(csv.DictReader(open(HERE / p)))
ext, main = load("omnet_results_ext.csv"), load("omnet_results_macos.csv")
f = lambda r, k: float(r[k])

# scheme (sim name) -> BASE Table IV/V row
MAP = {"Proposed_V1_T4": "Proposed scheme", "Poorambage": "Poorambage [11]", "Turkanovic_printed": "Turkanovic [12]",
       "Dhillon_Karla": "Dhillon-Karla [13]", "ChengLe_printed": "Cheng-Le [14]", "Jiang15_printed": "Jiang [15]",
       "Shuai16_printed": "Shuai [16]", "Wazid": "Wazid [17]", "Sadhukhan": "Sadhukhan [18]"}
def cost(ops): return sum(T3[k] * n for k, n in (ops or {}).items())

print("== 1. Table IV bits and Table V x Table III per-session cost, no adversaries, N = 100 (uncontended; proposed with hash-indexed lookup) ==\nCONSISTENCY CHECK: bits and ops are inputs to the model, so equality here confirms the pipeline, not the paper.")
print(f"{'scheme':20s} {'Tbl IV bits':>11s} {'sim bits/sess':>13s}  {'Tbl V dev+srv ms':>16s} {'sim latency ms':>15s}")
ok = True
for s, row in MAP.items():
    rs = [r for r in ext if r["config"] == (f"AH_{s}__BASE" if s == "Proposed_V1_T4" else f"A_{s}__BASE")]
    bits = st.mean(f(r, "kbit_on_air") * 1000 / f(r, "sessions_completed") for r in rs)
    lat = st.mean(f(r, "latency_mean_ms") for r in rs)
    t5 = T5[row]; ops = cost(t5.get("device")) + cost(t5.get("server"))
    exact = abs(bits - T4[row][4]) < 1e-6
    ok &= exact
    print(f"{s:20s} {T4[row][4]:11d} {bits:13.3f}{'  OK' if exact else '  MISMATCH'} {ops:16.3f} {lat:15.3f}")
print("Table IV bits reproduced exactly for all schemes:", ok)

def mean_at(rows, cfg, n, k="latency_mean_ms"):
    v = [f(r, k) for r in rows if r["config"] == cfg and int(r["N"]) == n]; return st.mean(v), (st.stdev(v) if len(v) > 1 else 0)

print("\n== 2. Ranking by mean authentication latency (ms) at N = 1000, BASE constants, 5% adversaries, 5 seeds ==")
rows = []
for s in MAP:
    if s == "Proposed_V1_T4": continue
    rows.append((s, *mean_at(main, f"M_{s}__BASE", 1000)))
rows.append(("Proposed (linear pseudonym scan)", *mean_at(main, "M_Proposed_V1_T4__BASE", 1000)))
rows.append(("Proposed (hash-indexed lookup)", *mean_at(ext, "H_Proposed_V1_T4__BASE", 1000)))
for i, (n, m, sd) in enumerate(sorted(rows, key=lambda r: r[1]), 1): print(f"{i:2d}. {n:34s} {m:12.3f} +/- {sd:8.3f}")

print("\n== 3. Ranking by kbit on air at N = 1000 (adversary traffic included) ==")
rows = []
for s in MAP: rows.append((s, *mean_at(main, f"M_{s}__BASE", 1000, "kbit_on_air")))
for i, (n, m, sd) in enumerate(sorted(rows, key=lambda r: r[1]), 1): print(f"{i:2d}. {n:22s} {m:10.1f}")

print("\n== 4. Figs. 1-2 axis (300..1800 devices): proposed latency (ms), linear scan vs hash index vs Dhillon-Karla ==")
ax = [300, 600, 900, 1200, 1500, 1800]
fig = load("omnet_results_macos.csv")
print("N        ", *[f"{n:>10d}" for n in ax])
for lab, rr, cfg in (("linear", fig, "F_Proposed_V1_T4__BASE"), ("hash", ext, "HF_Proposed_V1_T4__BASE"), ("Dhillon", fig, "F_Dhillon_Karla__BASE")):
    print(f"{lab:9s}", *[f"{mean_at(rr, cfg, n)[0]:10.3f}" for n in ax])

print("\n== 5. Does the processing ranking survive charging the User/Client column too? (Table V x Table III, no simulation) ==")
tot = {r: cost(T5[r].get("user")) + cost(T5[r].get("device")) + cost(T5[r].get("server")) for r in MAP.values()}
for i, (n, v) in enumerate(sorted(tot.items(), key=lambda kv: kv[1]), 1): print(f"{i:2d}. {n:22s} {v:9.3f} ms")
print("Proposed rank by total cost incl. user column:", sorted(tot, key=tot.get).index("Proposed scheme") + 1, "of", len(tot))

try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, json
    pub = json.load(open(HERE.parent / "baseline" / "published_baseline.json"))["figures"]["fig1"]
    fg, axs = plt.subplots(1, 2, figsize=(11, 4))
    for name, vals in pub["series"].items(): axs[0].plot(pub["x"], vals, marker="o", label=name)
    axs[0].set(title="Published Fig. 1 (as plotted; 'Communication Overhead %')", xlabel="Vehicles in VANET", ylabel="% (unit as labelled)"); axs[0].legend(fontsize=7)
    for lab, rr, cfg in (("Proposed, linear pseudonym scan", fig, "F_Proposed_V1_T4__BASE"), ("Proposed, hash-indexed lookup", ext, "HF_Proposed_V1_T4__BASE"),
                         ("Dhillon-Karla", fig, "F_Dhillon_Karla__BASE"), ("Jiang (as printed)", fig, "F_Jiang15_printed__BASE"), ("Sadhukhan", fig, "F_Sadhukhan__BASE")):
        axs[1].plot(ax, [mean_at(rr, cfg, n)[0] for n in ax], marker="o", label=lab)
    axs[1].set(yscale="log", title="Simulated (OMNeT++, BASE Table II/III constants)", xlabel="Devices", ylabel="mean authentication latency (ms, log)"); axs[1].legend(fontsize=7)
    fg.tight_layout(); fg.savefig(HERE.parent / "baseline" / "published_vs_simulated.png", dpi=150); print("\nwrote baseline/published_vs_simulated.png")
except ImportError:
    print("matplotlib not available: figure skipped")
