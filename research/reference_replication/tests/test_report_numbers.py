"""Every number quoted in REPORT.md that has a source in results/ or in the paper tables must match it."""
import csv
import re
import step2_reproduce as s2
import refmodel as M
from common import ROOT, RESULTS, T3, T4, T5, T6, load_extracted

REPORT = (ROOT / "REPORT.md").read_text(encoding="utf8")


def has(s):
    assert s in REPORT, f"REPORT.md does not contain {s!r}"


def comma(x, nd=0):
    return f"{x:,.{nd}f}"


def omnet_main():
    return {(r["environment"], r["scheme"], int(r["N"])): r for r in csv.DictReader(open(RESULTS / "step5b_omnet_main.csv", encoding="utf8"))}


def omnet_sens():
    return {(r["config"], int(r["N"])): r for r in csv.DictReader(open(RESULTS / "step5b_omnet_sensitivity.csv", encoding="utf8"))}


def test_changle_p2_mismatch_quoted_correctly():
    r = [x for x in s2.changle(load_extracted()) if x[0] == "TIII P2 user"][0]
    assert r[2] == 0.12765 and r[3] == 0.12965
    has("0.12765") ; has("0.12965")


def test_step3_and_table_facts_quoted():
    assert (T5["Turkanovic [12]"]["device"]["H"], T5["Turkanovic [12]"]["server"]["H"]) == (7, 5)
    has("7/7/5") ; has("7/5/7")
    has("T_C = 32.40 ms")
    assert T3["C"] == T3["H"] == 0.32 and round(32.40 / 0.32) == 101
    has("101x")


def test_table_iii_and_v_derived_numbers():
    t = M.const_A(17.3)
    assert abs(M.scheme_costs(M.PROPOSED["V1 Table V as printed"], t)[3] - 23.68) < 1e-9
    has("23.68")
    tot = {n: M.scheme_costs(M.base_printed()[n], t)[4] for n in ("Turkanovic [12]", "Dhillon-Karla [13]", "Jiang [15]")}
    assert [round(v, 2) for v in tot.values()] == [6.08, 7.04, 7.04]
    has("6.08/7.04/7.04")


def test_ours_percentages_quoted():
    comp = {k: v[4] for k, v in T4.items() if not k.startswith("Proposed")}
    r = M.reductions(comp, 1024)
    assert (round(r["vs best"], 1), round(r["vs mean"], 1)) == (36.0, 57.5)
    has("36.0%") ; has("57.5%")
    sv = {k: v[0] for k, v in T6.items() if k != "Proposed scheme"}
    dv = {k: v[1] for k, v in T6.items() if k != "Proposed scheme"}
    assert round(M.reductions(dv, 320)["vs best"], 1) == 10.1 and round(M.reductions(sv, 320)["vs best"], 1) == 33.3


def test_ecc_ratio_range_quoted():
    allr = []
    for aes in ("aes_big", "aes_ct"):
        t = M.const_C(80, aes)
        p = M.scheme_costs(M.PROPOSED["V1 Table V as printed"], t)[3]
        for n in ("Sadhukhan [18]", "Shuai [16]", "Cheng-Le [14]", "Challa et al. [17]", "Poorambage [11]"):
            allr.append(M.scheme_costs(M.base_printed()[n], t)[3] / p)
    assert round(min(allr)) == 60 and round(max(allr)) == 2520
    has("60x") ; has("2,520x")


def test_tc_crossovers_quoted():
    rows = list(csv.DictReader(open(RESULTS / "step4_tc_sensitivity.csv", encoding="utf8")))
    v = [float(r["T_C_crossover_ms"]) for r in rows]
    assert round(min(v), 2) == 0.14 and round(max(v), 1) == 5.2
    has("0.14-5.2 ms")


def test_omnet_sensitivity_numbers_quoted():
    S = omnet_sens()
    g = lambda c, n, k="latency_mean_ms": float(S[(c, n)][k])
    pre = "Proposed_V1_T4__MEAS"
    for cfg, n, nd in ((pre + "__adv0p05", 1000, 0), (pre + "__adv0p0", 1000, 0), (pre + "__adv0p1", 1000, 0), (pre + "__range800", 1000, 0),
                       (pre + "__nearest", 1000, 1), ("Proposed_V1_T4__MEAS_LAP", 1000, 2), ("Dhillon_Karla__MEAS_LAP", 1000, 2)):
        has(comma(g(cfg, n), nd))
    has(comma(g(pre + "__adv0p05", 1000, "latency_p95_ms")))
    # run-to-run spread: 35% in the reference case, up to 77% elsewhere (as quoted)
    rel = {c: float(r["latency_mean_sd"]) / float(r["latency_mean_ms"]) for (c, n), r in S.items()
           if c.startswith("Proposed_V1_T4__") and n == 1000 and float(r["latency_mean_ms"]) > 100}
    assert round(rel[pre + "__adv0p05"], 2) == 0.35 and round(max(rel.values()), 2) == 0.77
    has("35% of the mean in the reference case and up to 77%")


def test_omnet_main_table_quoted():
    M_ = omnet_main()
    for env, sch, n in (("BASE", "Proposed_V1_T4", 1000), ("MEAS", "Proposed_V1_T4", 1000), ("BASE", "Dhillon_Karla", 100), ("MEAS", "Sadhukhan", 1000), ("MEAS", "JIANG_published", 100)):
        r = M_[(env, sch, n)]
        assert comma(float(r["server_busy_total_ms"])) in REPORT, (env, sch, n)
        assert comma(float(r["kbit_on_air"])) in REPORT, (env, sch, n)


def test_finding7_orderings_hold_in_every_variant():
    """Report Finding 7: in every sensitivity variant the proposed scheme has fewer bits/energy than the comparison schemes
    and more latency and server work than the hash-only scheme run in the same variant."""
    S = omnet_sens()
    variants = sorted({c.split("__", 1)[1] for (c, n) in S if c.startswith("Proposed_V1_T4__")})
    checked = 0
    for v in variants:
        for n in (100, 1000):
            p, d, sad = (S.get((f"{s}__{v}", n)) for s in ("Proposed_V1_T4", "Dhillon_Karla", "Sadhukhan"))
            if p is None or d is None:
                continue
            checked += 1
            assert float(p["latency_mean_ms"]) > float(d["latency_mean_ms"]), (v, n)
            assert float(p["server_busy_total_ms"]) > float(d["server_busy_total_ms"]), (v, n)
            assert float(p["kbit_on_air"]) < float(d["kbit_on_air"]), (v, n)
            if sad is not None:
                assert float(p["kbit_on_air"]) < float(sad["kbit_on_air"]), (v, n)
    assert checked >= 20


def test_section_a_table_is_the_generated_one():
    """Section A of REPORT.md embeds results/step7_section.md verbatim, so every number in it comes from step7_base_vs_ours.py."""
    for line in (RESULTS / "step7_section.md").read_text(encoding="utf8").strip().splitlines():
        assert line in REPORT


def test_papers_environment_table_quoted():
    M_ = omnet_main()
    for sch in ("Proposed_V1_T4", "Turkanovic_corrected", "Dhillon_Karla", "ChangLe_P1", "ChengLe_as_P2", "JIANG_published"):
        for n in (100, 1000):
            r = M_[("PAPERS", sch, n)]
            row = f"{comma(float(r['latency_mean_ms']), 1)} / {comma(float(r['server_busy_total_ms']))} / {comma(float(r['kbit_on_air']))} / {float(r['energy_mJ']):.1f}"
            assert row in REPORT, (sch, n, row)
    ranks = {(r["environment"], r["metric"], r["proposed_reading"]): r for r in csv.DictReader(open(RESULTS / "step5b_omnet_ranks_N1000.csv", encoding="utf8"))}
    assert ranks[("PAPERS", "latency_mean_ms", "Proposed_V1_T4")]["rank_1_lowest"] == "7"
    assert ranks[("PAPERS", "server_busy_total_ms", "Proposed_V1_T4")]["rank_1_lowest"] == "6"
    assert ranks[("PAPERS", "kbit_on_air", "Proposed_V1_T4")]["rank_1_lowest"] == "2"
    has("ranks 7th of 8 by latency, 6th of 8 by server busy time")


def test_environment_mismatch_numbers():
    assert round(32.40 / 0.32) == 101 and round(63.075 / 17.1, 1) == 3.7 and round(0.32 / 0.20, 1) == 1.6 and round(0.32 / 0.5, 2) == 0.64
    assert round(M.scheme_costs(M.jiang_published(), {"H": 0.32, "C": 0.32})[3], 2) == 5.44
    assert round(M.scheme_costs(M.jiang_published(), {"H": 0.20, "C": 32.40})[3], 1) == 196.6
    has("5.4 ms (cheaper than the proposed scheme) to 196.6 ms")
