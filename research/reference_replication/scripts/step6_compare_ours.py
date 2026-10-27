#!/usr/bin/env python3
"""Step 6: test each quantitative claim of OURS (paper/main.tex) against Steps 2-5. Numbers are computed here, verdicts are ours.
Verdict vocabulary: REPRODUCED / PARTIAL / CONTRADICTED / NOT TESTABLE HERE (needs hardware we do not have in this study)."""
import csv
import statistics as st
import refmodel as M
from common import write_csv, RESULTS, T3, T4, T5, T6, AUDIT


def ratios_ecc(t):
    ecc = {"Sadhukhan": M.base_printed()["Sadhukhan [18]"], "Shuai [16] (BASE row)": M.base_printed()["Shuai [16]"],
           "Cheng-Le [14] (BASE row)": M.base_printed()["Cheng-Le [14]"], "Challa [17]": M.base_printed()["Challa et al. [17]"],
           "Poorambage": M.base_printed()["Poorambage [11]"]}
    p = M.scheme_costs(M.PROPOSED["V1 Table V as printed"], t)[3]
    return p, {k: M.scheme_costs(v, t)[3] / p for k, v in ecc.items()}, {k: M.scheme_costs(v, t)[3] for k, v in ecc.items()}


def main():
    R = []

    def add(cid, claim, verdict, evidence):
        R.append((cid, claim, verdict, evidence))

    # C1 16x
    add("C1", "P-256 scalar mult on ESP8266 is 16x the assumed 17.1 ms (276 ms)", "NOT TESTABLE HERE (model-level arithmetic only)",
        f"276.35 / 17.1 = {276.35/T3['ECM']:.2f} from results/esp8266_80mhz.csv (existing measurement; no hardware re-measured in this study). Ratio T_ECM/T_H measured = {276.35/0.036342:.0f} vs BASE {T3['ECM']/T3['H']:.0f}.")
    # C2 120-3000x
    parts = []
    for aes in ("aes_big", "aes_ct"):
        p, r, c = ratios_ecc(M.const_C(80, aes))
        parts.append(f"{aes}: proposed V1 {p:.2f} ms; " + ", ".join(f"{k} {c[k]:.0f} ms ({r[k]:.0f}x)" for k in r))
    allr = [v for aes in ("aes_big", "aes_ct") for v in ratios_ecc(M.const_C(80, aes))[1].values()]
    add("C2", "Proposed is about 120-3000x cheaper than the ECC-based schemes (ESP8266 80 MHz, V1)", "PARTIAL (order of magnitude holds; stated end points do not)",
        f"computed like-for-like range {min(allr):.0f}x-{max(allr):.0f}x (not 120-3000x). " + " | ".join(parts) +
        ". The 60x low end is Sadhukhan with aes_ct; 2520x is Poorambage with aes_big; 3000x is not reached. 'Shuai [16]' and 'Cheng-Le [14]' are BASE rows with wrong references (F4, F7); taking Cheng-Le as CHANGLE P2 leaves its cost unchanged (same 2 T_ECM + 12 T_H), dropping Shuai removes one of five ratios but not the extremes. Challa uses the unmeasured T_fe.")
    # C3 hash-only cheaper, per reading and T_C
    lines = []
    for clk in (80, 160):
        for tc in (0.32, 32.40):
            t = M.const_C(clk, "aes_big", tc)
            pair = [M.turkanovic_corrected(), M.base_printed()["Dhillon-Karla [13]"]]
            for k, v in M.PROPOSED.items():
                pr = M.scheme_costs(v, t)
                n2 = sum(M.scheme_costs(s_, t)[3] < pr[3] for s_ in pair)
                jc = M.scheme_costs(M.jiang_published(), t)[3] < pr[3]
                lines.append(f"{clk}MHz T_C={tc} {k[:2]}: Turk+Dhillon {n2}/2, JIANG {'cheaper' if jc else 'NOT cheaper'}")
    add("C3", "All three hash-only schemes (Turkanovic, Dhillon-Karla, Jiang) cost less than the proposed scheme in every column, V1-V4 (OURS Table II, ESP8266 3/3)", "PARTIAL",
        "With BASE's rows as printed the 3/3 reproduces (Step 4 ranks). Turkanovic and Dhillon-Karla (both hash-only in their originals) are cheaper in every case below. JIANG as published (11 T_H + 6 T_C, not hash-only): " +
        "; ".join(lines) + ". JIANG's role split is unavailable, so only the combined (device+server) column can be compared.")
    # C4 hash-only trio total costs
    tot = lambda n: sum(T5[n][r]["H"] for r in ("user", "device", "server")) * T3["H"]
    add("C4", "Table V under Table III: proposed 23.7 ms; hash-only 6.1, 7.0, 7.0 ms (all roles)", "REPRODUCED",
        f"Turkanovic {tot('Turkanovic [12]'):.2f}, Dhillon-Karla {tot('Dhillon-Karla [13]'):.2f}, Jiang[15] {tot('Jiang [15]'):.2f}; proposed V1 dev+srv {M.scheme_costs(M.PROPOSED['V1 Table V as printed'], M.const_A(17.3))[3]:.2f} ms. "
        f"JIANG as published under BASE constants and T_C = 0.32: {M.scheme_costs(M.jiang_published(), M.const_A(17.3))[3]:.2f} ms (P2+P3); under JIANG's own constants {11*0.2+6*32.4:.1f} ms.")
    # C5 comm
    comp = {k: v[4] for k, v in T4.items() if not k.startswith("Proposed")}
    rd = M.reductions(comp, 1024)
    add("C5", "Table IV gives 36.0% fewer bits than the best competitor and 57.5% fewer than the mean", "REPRODUCED (arithmetic) / label-dependent",
        f"vs best {rd['vs best']:.1f}%, vs mean {rd['vs mean']:.1f}%. Rows 'Jiang [15]' and 'Shuai [16]' contradict JIANG's own 1312/1584 bits (F11); replacing both by 1312 gives best-competitor reduction "
        f"{M.reductions({**{k: v for k, v in comp.items() if k not in ('Jiang [15]', 'Shuai [16]')}, 'JIANG': 1312}, 1024)['vs best']:.1f}% (exploratory: JIANG has 2 rounds, BASE counts 4 messages for everyone). Bit counts for the other rows are UNVERIFIED (F3, F6).")
    # C6 storage
    sv = {k: v[0] for k, v in T6.items() if k != "Proposed scheme"}; dv = {k: v[1] for k, v in T6.items() if k != "Proposed scheme"}
    add("C6", "Table VI gives 10.1% (device) and 33.3% (server) less storage than the best competitor", "REPRODUCED (arithmetic); source rows UNVERIFIED",
        f"device vs best {M.reductions(dv, 320)['vs best']:.1f}%, server vs best {M.reductions(sv, 320)['vs best']:.1f}%. None of JIANG/DHILLON/CHANGLE gives a storage table, so no Table VI row can be checked against these three originals.")
    # C7 17/21/12 not derivable
    allp = {}
    for name, t in (("A V1 dev+srv", M.const_A(17.3)),):
        comp = {k: M.scheme_costs(v, t)[3] for k, v in M.base_printed().items()}
        allp[name] = M.reductions(comp, M.scheme_costs(M.PROPOSED["V1 Table V as printed"], t)[3])
    hit = [(k, d, round(v, 1)) for k, d, v in [(n, dn, vv) for n, x in allp.items() for dn, vv in x.items()] if abs(v - 21) < 1]
    add("C7", "The headline 17%/21%/12% cannot be derived from Tables IV-VI (nine definitions)", "REPRODUCED for the table-applicable definitions",
        f"processing (Table V x III, V1): {', '.join(f'{d} {v:.1f}%' for d, v in next(iter(allp.values())).items())}; communication: vs best 36.0, mean 57.5; storage: 10.1 / 33.3 / etc. within-1-point hits for 21%: {hit or 'none'}. "
        "Only five of the nine definitions apply to a table (best, mean, median, worst, ratio-of-sums~mean); the other four average over a figure's x-axis and were not re-run here (they need the digitised figure values).")
    # C8 4-11x
    rr = []
    for aes in ("aes_big", "aes_ct"):
        t = M.const_C(80, aes)
        for k, v in M.PROPOSED.items():
            p = M.scheme_costs(v, t)[3]
            for n, s in (("Turkanovic", M.turkanovic_corrected()), ("Dhillon-Karla", M.base_printed()["Dhillon-Karla [13]"]), ("Jiang[15]", M.base_printed()["Jiang [15]"])):
                rr.append((aes, k[:2], n, p / M.scheme_costs(s, t)[3]))
    v1 = [r[3] for r in rr if r[1] == "V1"]
    allr2 = [r[3] for r in rr]
    add("C8", "On the ESP8266 the proposed scheme is 4-11x more expensive than the hash-only schemes", "REPRODUCED (arithmetic); third scheme is BASE's row",
        f"V1: {min(v1):.1f}-{max(v1):.1f}x; V1-V4 both AES: {min(allr2):.1f}-{max(allr2):.1f}x (dev+srv, GCM incl. key setup). Replacing BASE 'Jiang [15]' by JIANG published at T_C=0.32 ms gives a cost of {M.scheme_costs(M.jiang_published(), M.const_C(80,'aes_big',0.32))[3]:.2f} ms vs proposed V1 {M.scheme_costs(M.PROPOSED['V1 Table V as printed'], M.const_C(80,'aes_big',0.32))[3]:.2f} ms, i.e. under V1 the proposed scheme is already cheaper than JIANG as published even at BASE's T_C (JIANG/proposed = {M.scheme_costs(M.jiang_published(), M.const_C(80,'aes_big',0.32))[3]/M.scheme_costs(M.PROPOSED['V1 Table V as printed'], M.const_C(80,'aes_big',0.32))[3]:.2f}x); the 4-11x range therefore rests on only two verified schemes (Turkanovic, Dhillon-Karla) plus BASE's unverified row.")
    # C9 KDF dominates device columns
    t = M.const_C(80)
    add("C9", "HKDF costs 6-17 T_H, against 5-7 T_H for the hash-only device columns", "PARTIAL",
        f"HKDF/T_H on ESP8266 = {t['KDF']/t['H']:.1f} (existing measurement). Device columns of the two originals-verified schemes are Turkanovic 5 T_H (not 7: F1) and Dhillon-Karla 6 T_H; the third ('Jiang', 5 T_H) is BASE's unverified row. So the quoted range '5-7' becomes '5-6' for the two verified schemes; the conclusion (KDF > device columns) is unchanged.")
    # C10 server O(N)
    rows = list(csv.DictReader(open(RESULTS / "step5_netsim.csv", encoding="utf8")))
    def g(cfg, n, k, scheme="Proposed V1 (Table V)"):
        return float([r for r in rows if r["config"] == cfg and r["N_devices"] == str(n) and r["scheme"] == scheme][0][k])
    c1 = "devices ESP8266, server ESP8266, T_C=0.32, range 500, reachable"
    c2 = "devices ESP8266, server ESP8266, T_C=0.32, range 500, nearest-only"
    c3 = "devices ESP8266, server laptop, T_C=0.32, range 500, reachable"
    om = {(r["config"], r["N"]): r for r in csv.DictReader(open(RESULTS / "step5b_omnet_sensitivity.csv", encoding="utf8"))}
    o = lambda cfg, n: float(om[(cfg, str(n))]["latency_mean_ms"])
    pre = "Proposed_V1_T4__MEAS"
    add("C10", "Server pseudonym-lookup cost grows linearly with the number of devices (O(N x W)), vs constant in Table V", "PARTIAL: depends on guessed inputs (sensitivity, not evidence)",
        f"OMNeT++ sensitivity runs (our model, BASE Table II, measured ESP8266 constants), mean latency N=100 -> N=1000: server resolves every device in range, 5% adversaries: {o(pre+'__adv0p05',100):.1f} -> {o(pre+'__adv0p05',1000):.0f} ms; "
        f"same without adversaries {o(pre+'__adv0p0',100):.1f} -> {o(pre+'__adv0p0',1000):.0f} ms; each server resolves only its own devices ({g(c2,100,'mean_enrolled_per_server'):.0f} -> {g(c2,1000,'mean_enrolled_per_server'):.0f} per server): {o(pre+'__nearest',100):.1f} -> {o(pre+'__nearest',1000):.1f} ms; "
        f"laptop-class server: {o('Proposed_V1_T4__MEAS_LAP',100):.2f} -> {o('Proposed_V1_T4__MEAS_LAP',1000):.2f} ms; 800 m range: {o(pre+'__range800',1000):.0f} ms at N=1000. "
        "The independent SimPy model agrees (17.2 -> 683 ms, laptop 1.2 -> 1.8 ms, nearest-only 10.4 -> 16.6 ms). "
        "So the lookup cost scales with the number of devices a server must resolve, and whether that is 'all N' or ~20 depends on enrolment policy, server class and adversary load, none of which BASE specifies. OURS should state it as a conditional.")
    add("C11", "A precomputed PID table needs 1000 x 25 x 32 B = 800 KB", "REPRODUCED (arithmetic)", f"{1000*25*32/1000:.0f} KB. (Our measured window is 13 epochs, i.e. 416 KB; 25 is the upper end.)")
    # C12 forward secrecy open question
    add("C12", "'We did not check whether the compared ECC-based schemes provide forward secrecy' (open)", "NOW PARTLY ANSWERABLE",
        "CHANGLE Table IV: P2, Shi, Choi provide perfect forward secrecy; P1, Turkanovic, Li do not. JIANG Table 1 claims PFS for its scheme. So the hash-only comparators Turkanovic/P1 are like-for-like with the proposed scheme (no PFS) but JIANG and the ECC schemes are not.")
    # C13 Jiang classification
    add("C13", "'Jiang' is a hash-only scheme (OURS Sec IV-C, Table II); the proposed scheme costs more than all three in every column", "CONTRADICTED as stated",
        "JIANG (OURS ref [5]) uses 6 extended-chaotic-map operations per scheme and 4 in its authentication phase (Table 2), with T_C = 32.40 ms vs T_H = 0.20 ms. The hash-only 'Jiang' is BASE's row [15], a different, unidentified source. "
        "Result: the claim holds for two of the three schemes unconditionally and for the third only for the BASE row; for JIANG as published it holds only if T_C < the crossover in results/step4_tc_sensitivity.csv (0.14-5.2 ms depending on platform and reading), which is below JIANG's own 32.40 ms.")
    # C14 other OURS statements about BASE
    add("C14", "OURS Sec IV-A(4): 'two schemes share reference number [17]'", "CONFIRMED and EXTENDED",
        "Challa and Wazid both [17] confirmed on BASE p.7. Additionally [14], [15], [16] point to a VANET paper, a Wen et al. edge-AI magazine article and the JIANG chaotic-maps paper respectively, none of which matches the row label (F4, F5, F7, F8).")
    write_csv(RESULTS / "step6_claims.csv", ["id", "OURS claim", "verdict", "evidence (computed)"], R)
    for r in R:
        print(f"[{r[0]}] {r[2]}\n    {r[1]}\n    {r[3]}\n")


if __name__ == "__main__":
    main()
