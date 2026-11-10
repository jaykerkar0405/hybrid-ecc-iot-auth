# Copyright (c) 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur
# SPDX-License-Identifier: Apache-2.0
"""Sensitivity of the resolution results to the assumptions the base paper does not fix.

No new simulation is run. The script reads the committed cost model (cost_model.csv) and the committed OMNeT++
results (sim/results.csv), and computes the offered load of the mean server at N = 1000,

    rho = lam_h * (S + h(n) * T_H) + lam_a * f(n) * T_H + e(n) * T_H / epoch,

where n is the mean number of devices enrolled per server in the committed runs, lam_h = N / (servers * window) the
honest session rate per server, lam_a = adversaries * rate / servers the forged rate, S = 11.84 ms the paper's server
cost per session (Table V), and h, f, e the measured honest, forged and per-epoch probes. rho >= 1 means the server
cannot keep up and its queue grows for the whole window. One assumption is varied at a time from the baseline used in
the paper. The script also reports the simulated ranking with and without adversaries.

Run from the repository root: python -I evaluation/resolution/sensitivity.py > evaluation/resolution/sensitivity.txt
"""
import csv
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STRATS = ["O2", "O4", "MW", "CR", "O3", "TM", "O1"]
N = 1000
BASE = dict(adv_share=0.05, adv_rate=1.0, window=10.0, t_h=0.32e-3, enrol="reachable")
S = 11.84e-3   # server cost per session, Table V of the base paper
EPOCH = 10.0   # O4 epoch length (omnetpp.ini)

cost = defaultdict(dict)
with open(HERE / "cost_model.csv") as fh:
    for r in csv.DictReader(fh):
        cost[r["strategy"]][int(r["n"])] = (float(r["honest_probes"]), float(r["forged_probes"]), float(r["epoch_probes"]))

runs = defaultdict(list)
with open(HERE / "sim" / "results.csv") as fh:
    rows = list(csv.DictReader(fh))
for r in rows:
    if float(r["sessions_completed"]) > 0:
        runs[(r["config"], int(r["N"]))].append(float(r["latency_mean_ms"]))
geo = [r for r in rows if r["config"] == "R_O2" and int(r["N"]) == N]
servers = statistics.mean(float(r["n_servers"]) for r in geo)
n_reach = round(statistics.mean(float(r["mean_enrolled_per_server"]) for r in geo))
n_max = round(max(float(r["max_enrolled_per_server"]) for r in geo))
n_near = round(N / servers)  # "nearest" enrolment: a server knows only the devices attached to it


def rho(s, p):
    n = n_reach if p["enrol"] == "reachable" else n_near
    h, f, e = cost[s][n]
    lam_h = N / (servers * p["window"])
    lam_a = round(p["adv_share"] * N) * p["adv_rate"] / servers
    return lam_h * (S + h * p["t_h"]) + lam_a * f * p["t_h"] + e * p["t_h"] / EPOCH


def th_limit(s, p):
    """Largest T_H (ms) at which the mean server is not saturated (rho < 1)."""
    n = n_reach if p["enrol"] == "reachable" else n_near
    h, f, e = cost[s][n]
    lam_h = N / (servers * p["window"])
    lam_a = round(p["adv_share"] * N) * p["adv_rate"] / servers
    slope = lam_h * h + lam_a * f + e / EPOCH
    return float("inf") if slope == 0 else (1 - lam_h * S) / slope * 1e3


def order(p):
    return sorted(STRATS, key=lambda s: rho(s, p))


print(f"Committed runs at N={N}: {servers:.0f} servers, mean enrolled n={n_reach} (max {n_max}), "
      f"{N / servers:.0f} sessions per server per window")
print()
print("Simulated mean latency at N=1000 (ms), from sim/results.csv")
print(f"{'':4}{'no adversaries':>16}{'5% adversaries':>16}")
for s in STRATS:
    a = statistics.mean(runs[("H_" + s, N)])
    b = statistics.mean(runs[("R_" + s, N)])
    print(f"{s:4}{a:16.2f}{b:16.2f}")
rank_h = sorted(STRATS, key=lambda s: statistics.mean(runs[("H_" + s, N)]))
rank_r = sorted(STRATS, key=lambda s: statistics.mean(runs[("R_" + s, N)]))
print("ranking, no adversaries:", " ".join(rank_h))
print("ranking, 5% adversaries:", " ".join(rank_r))
print()
print("Offered load rho of the mean server at N=1000, one assumption varied at a time (rho >= 1: saturated)")
cases = [("baseline (paper)", {})]
cases += [(f"adversary share {v:.0%}", {"adv_share": v}) for v in (0.0, 0.10, 0.20)]
cases += [(f"adversary rate {v:g} Hz", {"adv_rate": v}) for v in (0.5, 2.0)]
cases += [(f"window {v:g} s", {"window": v}) for v in (5.0, 20.0)]
cases += [(f"T_H {v * 1e3:g} ms", {"t_h": v}) for v in (0.16e-3, 0.64e-3)]
cases += [("enrolment nearest", {"enrol": "nearest"})]
print(f"{'case':24}" + "".join(f"{s:>9}" for s in STRATS) + "  order by rho")
for name, ch in cases:
    p = {**BASE, **ch}
    print(f"{name:24}" + "".join(f"{rho(s, p):9.3f}" for s in STRATS) + "  " + " ".join(order(p)))
print()
print("Largest T_H (ms) at which the mean server is not saturated, baseline otherwise (paper: 0.32 ms)")
for s in STRATS:
    v = th_limit(s, BASE)
    print(f"{s:4}{'unbounded' if v == float('inf') else f'{v:10.4f}'}")
