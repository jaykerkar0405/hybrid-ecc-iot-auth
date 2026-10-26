#!/usr/bin/env python3
"""Step 4: score the proposed scheme and the reference schemes under one common environment, three constant sets:
 (A) BASE Table III, (B) each reference paper's own constants, (C) our measured ESP8266 80/160 MHz constants.
T_C is the extended-chaotic-map time; it is unmeasured on our hardware, so every set is run at T_C = 0.32 ms (BASE) and 32.40 ms (JIANG).
Outputs: results/step4_costs.csv, step4_ranks.csv, step4_reductions.csv, step4_tc_sensitivity.csv/.png"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import refmodel as M
from common import write_csv, RESULTS, T4

TC_BASE, TC_JIANG = 0.32, 32.40
KDF_RATIO = M.measured_kdf_ratio(80)   # HKDF-SHA256 / T_H measured on the ESP8266; BASE gives no KDF constant


def constant_sets():
    sets = {}
    for tc in (TC_BASE, TC_JIANG):
        a = M.const_A(KDF_RATIO); a["C"] = tc
        sets[f"A BASE Table III (KDF={KDF_RATIO:.1f} T_H, measured ratio) | T_C={tc}"] = a
        for clk in (80, 160):
            sets[f"C ESP8266 {clk} MHz measured (aes_big) | T_C={tc}"] = M.const_C(clk, "aes_big", tc)
        sets[f"C ESP8266 80 MHz measured (aes_ct) | T_C={tc}"] = M.const_C(80, "aes_ct", tc)
    return sets


def all_schemes():
    s = {}
    s.update({f"Proposed {k}": v for k, v in M.PROPOSED.items()})
    s.update(M.base_printed())
    s["Turkanovic [12] (corrected 7/5/7)"] = M.turkanovic_corrected()
    s["Cheng-Le [14] (as CHANGLE P2)"] = M.changle_schemes()["Chang-Le P2"]
    s["JIANG published (P2+P3)"] = M.jiang_published()
    s["JIANG published (P3 only)"] = M.jiang_p3_only()
    for k, v in M.changle_schemes().items():
        s[k] = v
    return s


def pools():
    return {"BASE-as-printed": M.base_printed(), "corrected": M.corrected_pool()}


def bits_for(name):
    if name.startswith("Proposed"):
        return None
    base = name.split(" (")[0]
    if base in T4:
        return T4[base][4]
    if name.startswith("JIANG published"):
        return 1312
    return None


def main():
    schemes = all_schemes(); sets = constant_sets(); cost_rows, rank_rows, red_rows = [], [], []
    pl = pools()
    for sname, t in sets.items():
        for n, s in schemes.items():
            u, d, v, ds, al = M.scheme_costs(s, t)
            cost_rows.append((sname, n, *(None if x is None else round(x, 6) for x in (u, d, v, ds, al)), bits_for(n)))
        # per-paper own constants (B) are added once, T_C independent
    B = M.const_B(); ch = B["CHANGLE"]; ji = B["JIANG"]
    Bsch = {"JIANG published (P2+P3) [own: T_H=0.2, T_C=32.4]": (M.jiang_published(), ji),
            "JIANG published (P3 only) [own]": (M.jiang_p3_only(), ji),
            "Chang-Le P1 [own: t_h=0.5]": (M.changle_schemes()["Chang-Le P1"], ch),
            "Chang-Le P2 [own: t_mul=63.075, t_h=0.5]": (M.changle_schemes()["Chang-Le P2"], ch),
            "Li et al. [CHANGLE 11] [own]": (M.changle_schemes()["Li et al. [CHANGLE 11]"], ch),
            "Turkanovic (corrected) [BORROWED CHANGLE t_h=0.5; Turkanovic/DHILLON give none]": (M.turkanovic_corrected(), ch),
            "Dhillon-Karla [BORROWED CHANGLE t_h=0.5; DHILLON gives no times]": (base_dh(), ch)}
    Bcost = {}
    for n, (s, t) in Bsch.items():
        u, d, v, ds, al = M.scheme_costs(s, t); Bcost[n] = (ds, al)
        cost_rows.append(("B own constants", n, *(None if x is None else round(x, 6) for x in (u, d, v, ds, al)), bits_for(n)))
    # proposed under BASE constants is the only available value for B (no constants of its own)
    ta = M.const_A(KDF_RATIO)
    for k, v in M.PROPOSED.items():
        u, d, vv, ds, al = M.scheme_costs(v, ta)
        Bcost[f"Proposed {k} [A constants]"] = (ds, al)
        cost_rows.append(("B own constants", f"Proposed {k} [A constants]", None, round(d, 6), round(vv, 6), round(ds, 6), round(al, 6), None))
    for k in M.PROPOSED:
        ps = Bcost[f"Proposed {k} [A constants]"][0]
        comp = {n: c[0] for n, c in Bcost.items() if not n.startswith("Proposed")}
        rk, ch_n = M.rank_of(ps, comp)
        rank_rows.append(("B own constants", "B-own pool", f"Proposed {k}", "dev+srv", round(ps, 4), rk, ch_n, len(comp), ";".join(n for n, x in comp.items() if x < ps)))
    # ranks and reductions per set
    for sname, t in sets.items():
        for pname, members in pl.items():
            for col, idx in (("dev+srv", 3), ("all roles", 4)):
                comp = {}
                for m, ops in members.items():
                    comp[m] = M.scheme_costs(ops, t)[idx]
                for k, v in M.PROPOSED.items():
                    pv = M.scheme_costs(v, t)[idx]
                    rk, cn = M.rank_of(pv, comp)
                    rank_rows.append((sname, pname, f"Proposed {k}", col, round(pv, 4), rk, cn, len(comp), ";".join(n for n, x in comp.items() if x is not None and x < pv)))
                    for dname, p in M.reductions(comp, pv).items():
                        red_rows.append((sname, pname, f"Proposed {k}", col, dname, round(p, 2)))
    bits_pools = {"BASE-as-printed (all 9 Table IV competitors)": {k: v[4] for k, v in T4.items() if k != "Proposed Scheme" and k != "Proposed scheme"},
                  "corrected (Jiang[15], Shuai[16] replaced by JIANG published 1312; others unverifiable, kept)": None}
    base = bits_pools["BASE-as-printed (all 9 Table IV competitors)"]
    corr = {k: v for k, v in base.items() if k not in ("Jiang [15]", "Shuai [16]")}
    corr["JIANG published (2 rounds)"] = 1312
    bits_pools = {"BASE-as-printed (all 9 Table IV competitors)": base, "corrected (Jiang[15], Shuai[16] -> JIANG 1312)": corr}
    for pname, comp in bits_pools.items():
        for label, pv in (("Table IV: 1024 bits", 1024), ("text Eq.21: 264 bits", 264), ("2 x 128 = 256 bits", 256)):
            for dname, p in M.reductions(comp, pv).items():
                red_rows.append(("bits (set-independent)", pname, label, "bits", dname, round(p, 2)))
    write_csv(RESULTS / "step4_costs.csv", ["constant_set", "scheme", "user_ms", "device_ms", "server_ms", "dev+srv_ms", "all_roles_ms", "bits"], cost_rows)
    write_csv(RESULTS / "step4_ranks.csv", ["constant_set", "pool", "proposed_reading", "column", "proposed_ms", "rank_1_is_cheapest", "n_competitors_cheaper", "n_competitors", "cheaper_competitors"], rank_rows)
    write_csv(RESULTS / "step4_reductions.csv", ["constant_set", "pool", "proposed_reading", "column", "definition", "pct_reduction"], red_rows)
    tc_sensitivity(schemes)
    summarize(rank_rows)


def base_dh():
    from common import T5
    return {r: M._conv(T5["Dhillon-Karla [13]"][r]) for r in ("user", "device", "server")}


def tc_sensitivity(schemes):
    rows = []; grid = np.logspace(np.log10(TC_BASE), np.log10(TC_JIANG), 41)
    plats = {"A BASE Table III": M.const_A(KDF_RATIO), "C ESP8266 80 MHz": M.const_C(80), "C ESP8266 160 MHz": M.const_C(160)}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharey=False)
    for ax, (pn, t0) in zip(axes, plats.items()):
        jp = M.jiang_published()["total"]
        for k, v in M.PROPOSED.items():
            ps = M.scheme_costs(v, t0)[3]
            tc_star = (ps - jp["H"] * t0["H"]) / jp["C"]
            rows.append((pn, k, round(ps, 4), round(tc_star, 4), "JIANG(published) cheaper than proposed iff T_C < T_C*", TC_BASE < tc_star, TC_JIANG < tc_star))
            ax.axhline(ps, ls="--", lw=1, label=f"Proposed {k.split()[0]}")
        ax.plot(grid, [jp["H"] * t0["H"] + jp["C"] * tc for tc in grid], color="k", lw=2, label="JIANG published (P2+P3)")
        for hn in ("Turkanovic [12] (corrected 7/5/7)", "Dhillon-Karla [13]"):
            ax.axhline(M.scheme_costs(schemes[hn], t0)[3], color="gray", ls=":", lw=1)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("T_C (ms)"); ax.set_title(pn + " (dev+srv, ms)")
        ax.axvline(TC_BASE, color="tab:blue", lw=.6); ax.axvline(TC_JIANG, color="tab:red", lw=.6)
    axes[0].set_ylabel("cost, ms (log)"); axes[0].legend(fontsize=7)
    fig.suptitle("Sensitivity to T_C: JIANG (published op count) vs proposed readings V1-V4; dotted = hash-only schemes")
    fig.tight_layout(); fig.savefig(RESULTS / "step4_tc_sensitivity.png", dpi=150); plt.close(fig)
    write_csv(RESULTS / "step4_tc_sensitivity.csv", ["platform", "proposed_reading", "proposed_dev+srv_ms", "T_C_crossover_ms", "meaning", "JIANG_cheaper_at_T_C=0.32", "JIANG_cheaper_at_T_C=32.40"], rows)


def summarize(rank_rows):
    print("\nRank of the proposed scheme (1 = cheapest) among the BASE-as-printed pool, dev+srv, per constant set and reading")
    for r in rank_rows:
        if r[1] == "BASE-as-printed" and r[3] == "dev+srv" and "T_C=0.32" in r[0]:
            print(f"  {r[0][:62]:62s} {r[2][9:11]} rank {r[5]:>2d}/{r[7]+1}  proposed {r[4]:9.3f} ms  cheaper: {len(r[8].split(';')) if r[8] else 0}")


if __name__ == "__main__":
    main()
