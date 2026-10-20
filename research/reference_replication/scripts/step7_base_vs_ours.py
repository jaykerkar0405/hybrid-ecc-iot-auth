#!/usr/bin/env python3
"""Step 7: head-to-head of what BASE's simulation reports against what OURS reports, with our replication in between.

Three environments (all use BASE Table II for the network, and BASE Tables IV/V for the bits and operation counts of the schemes):
  BASE   BASE Table III constants (T_H = T_C = 0.32, T_SE/D 5.6, T_ECM 17.1, T_fe 17.1 ms)
  PAPERS the constants of the three papers the compared schemes come from (JIANG T_H 0.20 / T_C 32.40; CHANGLE t_mul 63.075 / t_h 0.5;
         DHILLON gives none and borrows CHANGLE's t_h); the proposed scheme has no constants of its own and keeps BASE's
  MEAS   OURS: constants measured on the ESP8266 (research/paper_audit)
Outputs: results/step7_base_vs_ours.csv and results/step7_environments.png"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import refmodel as M
import gen_omnet_ini as G
from common import RESULTS, T3, T4, T5, T6, write_csv

DEV = lambda ops, t: M.scheme_costs(ops, t)[3]      # device + server, ms


def omnet(env, scheme, n, col):
    for r in csv.DictReader(open(RESULTS / "step5b_omnet_main.csv", encoding="utf8")):
        if r["environment"] == env and r["scheme"] == scheme and int(r["N"]) == n:
            return float(r[col])
    raise KeyError((env, scheme, n))


def fig_axis(scheme, n, col):
    for r in csv.DictReader(open(RESULTS / "step5b_omnet_fig_axis.csv", encoding="utf8")):
        if r["scheme"] == scheme and int(r["N"]) == n:
            return float(r[col])
    raise KeyError((scheme, n))


def processing_table():
    """device+server ms of the proposed scheme and of the scheme each paper contributes, in the three environments."""
    a = M.const_A(G.KDF_RATIO); c = M.const_C(80, "aes_big"); b = M.const_B()
    prop = M.PROPOSED["V1 Table V as printed"]
    rows = {"Proposed (V1)": (DEV(prop, a), DEV(prop, a), DEV(prop, c))}
    own = lambda ops, k: DEV(ops, k)
    cs = M.changle_schemes()
    rows["Turkanovic (7/5/7)  [CHANGLE, DHILLON]"] = (DEV(M.turkanovic_corrected(), a), own(M.turkanovic_corrected(), {"H": b["CHANGLE"]["H"]}), DEV(M.turkanovic_corrected(), c))
    rows["Dhillon-Karla  [DHILLON]"] = (DEV(M.base_printed()["Dhillon-Karla [13]"], a), own(M.base_printed()["Dhillon-Karla [13]"], {"H": b["CHANGLE"]["H"]}), DEV(M.base_printed()["Dhillon-Karla [13]"], c))
    rows["Chang-Le P1  [CHANGLE]"] = (DEV(cs["Chang-Le P1"], a), own(cs["Chang-Le P1"], b["CHANGLE"]), DEV(cs["Chang-Le P1"], c))
    rows["Chang-Le P2  [CHANGLE, ECC]"] = (DEV(cs["Chang-Le P2"], a), own(cs["Chang-Le P2"], b["CHANGLE"]), DEV(cs["Chang-Le P2"], c))
    ja = dict(a); ja["C"] = 0.32
    rows["JIANG published (T_C 0.32 BASE, 32.40 papers, 0.32 measured)  [JIANG]"] = (DEV(M.jiang_published(), ja), own(M.jiang_published(), b["JIANG"]), DEV(M.jiang_published(), M.const_C(80, "aes_big", 0.32)))
    return rows


def main():
    P = processing_table()
    R = []

    def add(i, metric, base, repl_base, repl_papers, ours, verdict):
        R.append((i, metric, base, repl_base, repl_papers, ours, verdict))

    prop = P["Proposed (V1)"]
    beat = lambda k: [n for n, v in P.items() if n != "Proposed (V1)" and v[k] < prop[k]]
    short = lambda names: ", ".join(n.split("  ")[0] for n in names) or "none"
    # 0 environment
    add("E1", "Environment: constants BASE used versus the constants of the three papers",
        f"Table III: T_H {T3['H']}, T_C {T3['C']}, T_ECM {T3['ECM']}, T_SE/D {T3['SE/D']}, T_fe {T3['fe']} ms",
        "same as BASE",
        "JIANG: T_H 0.20, T_C 32.40 ms. CHANGLE: t_h 0.5, t_mul 63.075 ms. DHILLON: none",
        "measured ESP8266: T_H 0.036, T_SE/D 0.48-1.15, T_ECM 276 ms (16x the 17.1)",
        "BASE's environment is not that of the papers its competitors come from: T_C is 101x lower than JIANG's, T_ECM 3.7x lower than CHANGLE's t_mul, and T_H is 1.6x JIANG's but 0.64x CHANGLE's")
    # 1 processing
    add("P1", "Processing: does the proposed scheme have the lowest cost? (device + server, ms)",
        "text Sec. V-A: 'minimum possible processing cost'; abstract ~21% lower; Table V gives counts only",
        f"BASE Table V x III: proposed {prop[0]:.1f} ms, rank {1 + len(beat(0))} of {len(P)}; cheaper: {short(beat(0))}",
        f"papers' constants: proposed {prop[1]:.1f} ms; cheaper: {short(beat(1))}; dearer: " + short([n for n in P if n != 'Proposed (V1)' and n not in beat(1)]),
        f"measured: proposed {prop[2]:.2f} ms; cheaper: {short(beat(2))}; ECC schemes 60-2,520x dearer; OURS: not the cheapest once the session KDF is counted",
        f"BASE's claim is NOT supported by its own Table V x III (rank {1 + len(beat(0))} of {len(P)}) nor by the papers' own constants against the hash-only schemes. It holds against the ECC scheme (Chang-Le P2) and against JIANG only when JIANG's own T_C = 32.40 ms is used, not with Table III's T_C = 0.32 ms. OURS agrees (and adds that the session KDF is missing from Table V)")
    # 2 OMNeT++ processing/latency
    lat = {e: omnet(e, "Proposed_V1_T4", 1000, "latency_mean_ms") for e in ("BASE", "PAPERS", "MEAS")}
    dh = {e: omnet(e, "Dhillon_Karla", 1000, "latency_mean_ms") for e in ("BASE", "PAPERS", "MEAS")}
    jg = {e: omnet(e, "JIANG_published", 1000, "latency_mean_ms") for e in ("BASE", "PAPERS", "MEAS")}
    allsch = ("Proposed_V1_T4", "Turkanovic_corrected", "Dhillon_Karla", "ChangLe_P1", "ChengLe_as_P2", "JIANG_published")
    rank = {e: 1 + sum(omnet(e, s_, 1000, "latency_mean_ms") < omnet(e, "Proposed_V1_T4", 1000, "latency_mean_ms") for s_ in allsch[1:]) for e in ("BASE", "PAPERS", "MEAS")}
    worst_nonecc = {e: all(omnet(e, "Proposed_V1_T4", 1000, "latency_mean_ms") > omnet(e, s_, 1000, "latency_mean_ms") for s_ in ("Turkanovic_corrected", "Dhillon_Karla", "ChangLe_P1", "JIANG_published")) for e in rank}
    add("P2", "Processing in the OMNeT++ model: mean authentication latency at N = 1000 (ms)",
        "Fig. 1 (Processing): proposed lowest, all curves rise with vehicles; values not tabulated",
        f"BASE env: proposed {lat['BASE']:,.0f}, Dhillon-Karla {dh['BASE']:.1f}, JIANG {jg['BASE']:.1f}",
        f"papers' env: proposed {lat['PAPERS']:,.0f}, Dhillon-Karla {dh['PAPERS']:.1f}, JIANG {jg['PAPERS']:,.0f}",
        f"measured env: proposed {lat['MEAS']:,.0f}, Dhillon-Karla {dh['MEAS']:.2f}, JIANG {jg['MEAS']:.2f}; OURS: lookup cost grows with devices per server",
        f"BASE's Fig. 1 claim (proposed lowest) is NOT reproduced in any environment: the proposed scheme ranks {rank['BASE']}/6 (BASE), {rank['PAPERS']}/6 (papers), {rank['MEAS']}/6 (measured) by latency; {'it is slower than every non-ECC scheme in all three environments' if all(worst_nonecc.values()) else 'it is not slower than every non-ECC scheme in every environment'}. The size is set by the pseudonym lookup, which BASE does not specify (nearest-only enrolment: see 8.5)")
    # 3 communication
    comp = {k: v[4] for k, v in T4.items() if not k.startswith("Proposed")}
    red = M.reductions(comp, 1024)
    kb = {s: omnet("BASE", s, 1000, "kbit_on_air") for s in ("Proposed_V1_T4", "Proposed_V1_text", "Dhillon_Karla", "JIANG_published", "Turkanovic_corrected")}
    add("C1", "Communication: bits",
        f"Table IV: proposed 1,024 bits (4 msgs) vs 1,600-3,360; {red['vs best']:.1f}% fewer than best, {red['vs mean']:.1f}% than mean; text: 264 bits, 2 msgs; abstract ~17%",
        f"OMNeT++ (N = 1000, kbit on air incl. forged traffic): proposed {kb['Proposed_V1_T4']:,.0f} (264-bit variant {kb['Proposed_V1_text']:,.0f}) vs JIANG {kb['JIANG_published']:,.0f}, Turkanovic {kb['Turkanovic_corrected']:,.0f}, Dhillon-Karla {kb['Dhillon_Karla']:,.0f}",
        "bits are identical in the papers' environment (sizes come from Table IV; JIANG's own 1,312 bits is used)",
        f"OURS: same arithmetic ({red['vs best']:.1f}% / {red['vs mean']:.1f}%), flags 4 msgs/1,024 bits vs 2 msgs/264 bits; 17% not derivable",
        "Direction REPRODUCED (proposed lowest in every variant); magnitude depends on 1,024 vs 264 bits and on the unverifiable competitor sizes; 17% not reproduced")
    # 4 storage
    sv = {k: v[0] for k, v in T6.items() if k != "Proposed scheme"}; dv = {k: v[1] for k, v in T6.items() if k != "Proposed scheme"}
    enr_r = omnet("BASE", "Proposed_V1_T4", 1000, "mean_enrolled_per_server")
    tbl_kb = enr_r * 13 * 32 / 1000
    add("S1", "Storage",
        f"Table VI: proposed 320 / 320 bits vs best {min(sv.values())} (server) / {min(dv.values())} (device); {M.reductions(sv, 320)['vs best']:.1f}% / {M.reductions(dv, 320)['vs best']:.1f}%; abstract ~12%",
        f"model: a server resolving every device in range holds ~{enr_r:.0f} enrolled devices at N = 1000; a precomputed pseudonym table of 13 epochs x 32 B is ~{tbl_kb:,.0f} KB (vs 40 B)",
        "not simulated (storage is not a simulated quantity); no storage table in JIANG, DHILLON or CHANGLE",
        "OURS: same arithmetic (10.1% / 33.3%); pseudonym lookup needs O(N x W) compute or storage (800 KB at 1,000 devices)",
        "Table VI arithmetic REPRODUCED, not 12%; the 320-bit server storage holds only if the server does not keep a per-device pseudonym table")
    # 5 scalability, BASE figure axis
    n1, n2 = 300, 1800
    add("F1", "Scaling with vehicles (BASE Figs. 1-2 axis, 300-1800 devices)",
        "curves rise slowly with vehicles; proposed lowest in Figs. 1-3",
        f"OMNeT++ BASE env: bits proposed {fig_axis('Proposed_V1_T4', n1, 'kbit_on_air'):,.0f} -> {fig_axis('Proposed_V1_T4', n2, 'kbit_on_air'):,.0f} kbit (lowest); latency proposed {fig_axis('Proposed_V1_T4', n1, 'latency_mean_ms'):,.0f} -> {fig_axis('Proposed_V1_T4', n2, 'latency_mean_ms'):,.0f} ms, Dhillon-Karla {fig_axis('Dhillon_Karla', n1, 'latency_mean_ms'):.1f} -> {fig_axis('Dhillon_Karla', n2, 'latency_mean_ms'):.1f} ms",
        "see section 8 (papers' environment curves in results/step5b_omnet_papers.png)",
        "OURS: Fig. 2 plots a fixed per-session bit cost rising with vehicles (22.4 -> 28.6 'bits'), impossible for a per-session protocol",
        "Communication ordering REPRODUCED; processing ordering NOT reproduced")
    # 6 abstract
    add("A1", "Abstract: ~17% communication, ~21% processing, ~12% storage",
        "17 / 21 / 12 %", "36.0 / 57.5 (comm), -517 / 68 (proc, best / mean), 10.1 / 33.3 (storage)", "not computable (no values)",
        "OURS: not derivable under any of the nine definitions", "NOT reproduced by BASE's own tables; consistent with OURS")
    write_csv(RESULTS / "step7_base_vs_ours.csv", ["id", "metric", "BASE reports", "replication in BASE environment", "replication in the three papers' environment", "OURS reports / measured", "verdict"], R)

    def cell(t):
        return t.replace("|", "/")
    lines = ["| topic | what BASE reports | same environment: our replication | what OURS reports | verdict |", "|---|---|---|---|---|"]
    for i, metric, base, rb, rp, ours, verdict in R:
        repl = f"**BASE environment:** {rb}. **Papers' environment:** {rp}." if i != "E1" else f"BASE: {base}. Papers: {rp}"
        lines.append(f"| {cell(metric)} | {cell(base if i != 'E1' else 'Table III as above')} | {cell(repl)} | {cell(ours)} | {cell(verdict)} |")
    (RESULTS / "step7_section.md").write_text(chr(10).join(lines) + chr(10), encoding="utf8")

    # figure: processing under the three environments
    names = list(P)
    x = np.arange(len(names)); w = 0.26
    fig, ax = plt.subplots(figsize=(11.5, 5))
    for k, (lab, col) in enumerate((("BASE Table III constants", "#8aa6c1"), ("constants of the three papers", "#d98c4a"), ("OURS: measured ESP8266", "#4a8f5a"))):
        ax.bar(x + (k - 1) * w, [P[n][k] for n in names], w, label=lab, color=col)
    ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels([n.replace("  ", "\n") for n in names], fontsize=7)
    ax.set_ylabel("device + server time (ms, log)"); ax.legend(fontsize=8)
    ax.set_title("Processing cost of the proposed scheme and of the schemes taken from the three papers, in the three environments (operation counts from BASE Table V)")
    ax.title.set_fontsize(9)
    fig.tight_layout(); fig.savefig(RESULTS / "step7_environments.png", dpi=130); plt.close(fig)
    for r in R:
        print(f"[{r[0]}] {r[1]}\n   BASE: {r[2]}\n   BASE env: {r[3]}\n   papers env: {r[4]}\n   OURS: {r[5]}\n   => {r[6]}\n")
    print({n: tuple(round(x, 3) for x in v) for n, v in P.items()})


if __name__ == "__main__":
    main()
