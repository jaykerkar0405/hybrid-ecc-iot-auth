#!/usr/bin/env python3
"""Aggregate OMNeT++ runs (results/omnet_results.csv, produced in WSL by omnet/run_omnet.sh) into tables and plots.
These runs are a SENSITIVITY ANALYSIS of a model we wrote ourselves (omnet/AuthNet.*), not evidence about the BASE protocol."""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import RESULTS, write_csv

SRC = RESULTS / "omnet_results.csv"
SCHEMES = ["Proposed_V1_T4", "Proposed_V2_T4", "Proposed_V1_text", "Turkanovic_corrected", "Dhillon_Karla", "Jiang15_printed",
           "JIANG_published", "ChangLe_P1", "Wazid", "ChengLe_as_P2", "Shuai16_printed", "Sadhukhan", "Poorambage"]
COLS = ["latency_mean_ms", "latency_p95_ms", "kbit_on_air", "energy_mJ", "server_busy_total_ms", "server_busy_max_ms", "mean_enrolled_per_server", "sessions_unreachable"]


def load():
    rows = list(csv.DictReader(open(SRC, encoding="utf8")))
    for r in rows:
        r["N"] = int(r["N"]); r["rep"] = int(r["rep"])
        for c in COLS + ["sessions_completed", "n_servers", "end_time_s"]:
            r[c] = float(r[c])
    return rows


def agg(rows):
    """(config, N) -> {col: (mean, sd)} over repetitions"""
    g = {}
    for r in rows:
        g.setdefault((r["config"], r["N"]), []).append(r)
    return {k: {c: (float(np.mean([x[c] for x in v])), float(np.std([x[c] for x in v], ddof=1)) if len(v) > 1 else 0.0) for c in COLS} | {"reps": len(v)} for k, v in g.items()}


def main():
    rows = load(); A = agg(rows)
    main_rows = []
    for (cfg, n), v in sorted(A.items()):
        if cfg.startswith("M_"):
            sch, env = cfg[2:].split("__")
            main_rows.append((env, sch, n, v["reps"], *(f"{v[c][0]:.4f}" for c in COLS), f"{v['latency_mean_ms'][1]:.4f}"))
    write_csv(RESULTS / "step5b_omnet_main.csv", ["environment", "scheme", "N", "reps"] + COLS + ["latency_mean_sd"], main_rows)

    for env, title in (("BASE", "BASE Table II environment, BASE Table III constants"), ("MEAS", "BASE Table II environment, measured ESP8266 constants"),
                       ("PAPERS", "BASE Table II environment, constants of the three papers (JIANG, CHANGLE; DHILLON borrows t_h)")):
        fig, axs = plt.subplots(2, 2, figsize=(12, 8.5))
        ax = axs.ravel()
        for i, s in enumerate(SCHEMES):
            xs = sorted(n for (c, n) in A if c == f"M_{s}__{env}")
            if not xs:
                continue
            for a, col, yl in zip(ax, ("latency_mean_ms", "kbit_on_air", "energy_mJ", "server_busy_total_ms"),
                                  ("mean latency (ms, log)", "kbit on air (log)", "radio energy (mJ, log)", "server busy time (ms, log)")):
                a.plot(xs, [A[(f"M_{s}__{env}", n)][col][0] for n in xs], marker="o", ms=3, label=s, color=plt.cm.tab20(i), ls="-" if i < 10 else "--")
                a.set(xlabel="devices", ylabel=yl, yscale="log")
        ax[0].legend(fontsize=7)
        fig.suptitle(f"OMNeT++ 6.0.3, our model - SENSITIVITY ANALYSIS - {title} (mean of 5 seeds)")
        fig.tight_layout(); fig.savefig(RESULTS / f"step5b_omnet_{env.lower()}.png", dpi=120); plt.close(fig)


    # BASE Figs. 1-2 x-axis (300..1800 devices), BASE environment
    figrows = []
    for (cfg, n), v in sorted(A.items()):
        if cfg.startswith("F_"):
            figrows.append((cfg[2:].replace("__BASE", ""), n, *(f"{v[c][0]:.4f}" for c in COLS[:6])))
    write_csv(RESULTS / "step5b_omnet_fig_axis.csv", ["scheme", "N"] + COLS[:6], figrows)
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
    for i, s_ in enumerate(SCHEMES):
        xs = sorted(n for (c, n) in A if c == f"F_{s_}__BASE")
        for a, col, yl in zip(ax, ("latency_mean_ms", "kbit_on_air", "server_busy_total_ms"), ("mean latency (ms, log)", "kbit on air (log)", "server busy time (ms, log)")):
            a.plot(xs, [A[(f"F_{s_}__BASE", n)][col][0] for n in xs], marker="o", ms=3, label=s_, color=plt.cm.tab20(i), ls="-" if i < 10 else "--")
            a.set(xlabel="devices (BASE Figs. 1-2 x-axis)", ylabel=yl, yscale="log")
    ax[0].legend(fontsize=6)
    fig.suptitle("OMNeT++ 6.0.3, our model, BASE Table II/III/IV, N = 300..1800 - SENSITIVITY ANALYSIS (mean of 5 seeds)")
    fig.tight_layout(); fig.savefig(RESULTS / "step5b_omnet_fig_axis.png", dpi=120); plt.close(fig)

    # sensitivity table at N = 1000 and N = 100
    sens = []
    for (cfg, n), v in sorted(A.items()):
        if cfg.startswith("S_") and n in (100, 1000):
            sens.append((cfg[2:], n, f"{v['latency_mean_ms'][0]:.3f}", f"{v['latency_mean_ms'][1]:.3f}", f"{v['latency_p95_ms'][0]:.3f}",
                         f"{v['server_busy_total_ms'][0]:.1f}", f"{v['kbit_on_air'][0]:.1f}", f"{v['mean_enrolled_per_server'][0]:.1f}", f"{v['sessions_unreachable'][0]:.1f}"))
    write_csv(RESULTS / "step5b_omnet_sensitivity.csv", ["config", "N", "latency_mean_ms", "latency_mean_sd", "latency_p95_ms", "server_busy_total_ms", "kbit_on_air", "mean_enrolled", "unreachable"], sens)

    # rank of the proposed scheme in the BASE environment at N=1000 (latency, server work, bits, energy), 1 = lowest
    rk = []
    for env in ("BASE", "MEAS", "PAPERS"):
        for col in ("latency_mean_ms", "server_busy_total_ms", "kbit_on_air", "energy_mJ"):
            vals = {s: A[(f"M_{s}__{env}", 1000)][col][0] for s in SCHEMES if (f"M_{s}__{env}", 1000) in A}
            order = sorted(vals, key=vals.get)
            for p in ("Proposed_V1_T4", "Proposed_V2_T4"):
                rk.append((env, col, p, order.index(p) + 1, len(order), f"{vals[p]:.3f}", ";".join(order[:order.index(p)])))
    write_csv(RESULTS / "step5b_omnet_ranks_N1000.csv", ["environment", "metric", "proposed_reading", "rank_1_lowest", "of", "value", "lower_than_proposed"], rk)
    # cross-check against the independent SimPy model (Step 5a), MEAS environment, same assumptions where they exist
    sp = {(r["scheme"], int(r["N_devices"])): r for r in csv.DictReader(open(RESULTS / "step5_netsim.csv", encoding="utf8"))
          if r["config"] == "devices ESP8266, server ESP8266, T_C=0.32, range 500, reachable"}
    pairs = {"Proposed_V1_T4": "Proposed V1 (Table V)", "Dhillon_Karla": "Dhillon-Karla", "Sadhukhan": "Sadhukhan (ECC)", "JIANG_published": "JIANG published"}
    cc = []
    for o, sname in pairs.items():
        for n in (100, 1000):
            v = A[(f"M_{o}__MEAS", n)]
            cc.append((o, n, f"{v['latency_mean_ms'][0]:.3f}", f"{v['latency_mean_ms'][1]:.3f}", sp[(sname, n)]["lat_mean_ms"],
                       f"{v['server_busy_total_ms'][0]:.1f}", sp[(sname, n)]["server_busy_ms_total"]))
    write_csv(RESULTS / "step5b_crosscheck_simpy.csv", ["scheme", "N", "omnet_latency_ms", "omnet_latency_sd", "simpy_latency_ms", "omnet_server_busy_ms", "simpy_server_busy_ms"], cc)
    print(f"{len(rows)} runs, {len(A)} (config,N) cells")
    for r in rk:
        print(r)


if __name__ == "__main__":
    main()
