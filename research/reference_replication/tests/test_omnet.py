"""Step 5 (OMNeT++): the generated ini is traceable to the paper tables, the sweep is complete, and results are physically sane."""
import csv
import re
import gen_omnet_ini as G
import refmodel as M
from common import ROOT, RESULTS, T3, T4

INI = ROOT / "omnet" / "omnetpp.ini"


def ini_section(name):
    txt = INI.read_text(encoding="utf8")
    m = re.search(r"\[Config " + re.escape(name) + r"\](.*?)(?=\n\[Config|\Z)", txt, re.S)
    assert m, name
    return dict(re.findall(r"^\*\.core\.(\w+) = (.+)$", m.group(1), re.M))


def test_general_section_has_base_table_ii_values():
    txt = INI.read_text(encoding="utf8")
    for line in ("network = AuthNet", "*.core.rateBps = 10e6", "*.core.quantumS = 15e-6", "*.core.handoffS = 10e-9",
                 "*.core.txPowerW = 0.0756", "*.core.rxPowerW = 0.0756", "*.serverFraction = 0.05", "*.core.rangeM = 500"):
        assert line in txt
    assert "# ASSUMPTIONS (not in BASE)" in txt


def test_dhillon_base_env_delays_come_from_table_iii_and_v():
    kv = ini_section("M_Dhillon_Karla__BASE")
    assert abs(float(kv["deviceProcMs"]) - 6 * T3["H"]) < 1e-6      # BASE Table V: device 6 T_H
    assert abs(float(kv["serverProcMs"]) - 8 * T3["H"]) < 1e-6      # server 8 T_H
    assert int(kv["bitsTotal"]) == T4["Dhillon-Karla [13]"][4] == 2528


def test_proposed_variants_and_jiang_traceable():
    assert int(ini_section("M_Proposed_V1_T4__BASE")["bitsTotal"]) == 1024
    k = ini_section("M_Proposed_V1_text__BASE")
    assert int(k["bitsTotal"]) == 264 and int(k["nMessages"]) == 2 and k["pseudonymLookup"] == "true"
    j = ini_section("M_JIANG_published__BASE")
    assert int(j["bitsTotal"]) == 1312 and int(j["nMessages"]) == 2
    t = G.envs(0.32)["BASE"][0]
    assert abs((float(j["deviceProcMs"]) + float(j["serverProcMs"])) - 11 * t["H"] - 6 * t["C"]) < 1e-5


def test_turkanovic_corrected_swaps_columns_only():
    p, c = ini_section("M_Turkanovic_printed__BASE"), ini_section("M_Turkanovic_corrected__BASE")
    assert abs(float(p["deviceProcMs"]) - float(c["serverProcMs"])) < 1e-9 and abs(float(p["serverProcMs"]) - float(c["deviceProcMs"])) < 1e-9
    assert p["bitsTotal"] == c["bitsTotal"]


def load():
    return list(csv.DictReader(open(RESULTS / "omnet_results.csv", encoding="utf8")))


def test_sweep_is_complete():
    rows = load()
    main = [r for r in rows if r["config"].startswith("M_")]
    sens = [r for r in rows if r["config"].startswith("S_")]
    fig = [r for r in rows if r["config"].startswith("F_")]
    n_main = 15 * 2 + len(G.PAPERS_SCHEMES)          # 15 schemes x {BASE, MEAS} + the PAPERS environment
    assert len(main) == n_main * 10 * 5 and len(sens) == 69 * 3 * 5 and len(fig) == 15 * 6 * 5
    assert len({r["config"] for r in rows}) == n_main + 69 + 15
    assert {r["rep"] for r in rows} == {"0", "1", "2", "3", "4"}
    assert {int(r["N"]) for r in fig} == {300, 600, 900, 1200, 1500, 1800}


def test_papers_environment_uses_each_papers_own_constants():
    j = ini_section("M_JIANG_published__PAPERS")
    assert abs(float(j["deviceProcMs"]) + float(j["serverProcMs"]) - (11 * 0.20 + 6 * 32.40)) < 1e-6      # JIANG: T_H 0.20, T_C 32.40 ms
    c = ini_section("M_ChengLe_as_P2__PAPERS")
    assert abs(float(c["deviceProcMs"]) - (2 * 63.075 + 5 * 0.5)) < 1e-6 and abs(float(c["serverProcMs"]) - 9 * 0.5) < 1e-6   # CHANGLE P2
    d = ini_section("M_Dhillon_Karla__PAPERS")
    assert abs(float(d["deviceProcMs"]) - 6 * 0.5) < 1e-6 and abs(float(d["serverProcMs"]) - 8 * 0.5) < 1e-6   # DHILLON counts x borrowed t_h


def test_mobile_variant_exists_and_is_not_a_different_regime():
    rows = load()
    for env in ("BASE", "MEAS"):
        st = mean(rows, f"S_Dhillon_Karla__{env}__adv0p05", 1000, "latency_mean_ms")
        mo = mean(rows, f"S_Dhillon_Karla__{env}__mobile160", 1000, "latency_mean_ms")
        assert abs(st - mo) / st < 0.01
    ini = INI.read_text(encoding="utf8")
    assert "speedMps = 44.4444" in ini      # 160 km/h, BASE Table II


def mean(rows, cfg, n, col):
    v = [float(r[col]) for r in rows if r["config"] == cfg and int(r["N"]) == n]
    assert len(v) == 5
    return sum(v) / 5


def test_hash_only_latency_is_compute_plus_airtime_and_flat_in_n():
    rows = load()
    a, b = mean(rows, "M_Dhillon_Karla__BASE", 100, "latency_mean_ms"), mean(rows, "M_Dhillon_Karla__BASE", 1000, "latency_mean_ms")
    compute = 14 * T3["H"]                       # 6 + 8 T_H
    airtime = 2528 / 10e6 * 1e3
    assert compute + airtime - 0.05 < a < compute + airtime + 0.5 and abs(a - b) < 0.2


def test_coverage_grows_with_servers():
    rows = load()
    u100 = mean(rows, "M_Dhillon_Karla__BASE", 100, "sessions_unreachable") / 100
    u1000 = mean(rows, "M_Dhillon_Karla__BASE", 1000, "sessions_unreachable") / 1000
    assert u100 > 0.1 and u1000 < 0.01


def test_assumption_sensitivities_move_in_the_expected_direction():
    rows = load()
    base = mean(rows, "S_Proposed_V1_T4__MEAS__adv0p05", 1000, "latency_mean_ms")
    assert mean(rows, "S_Proposed_V1_T4__MEAS__nearest", 1000, "latency_mean_ms") < base / 10
    assert mean(rows, "S_Proposed_V1_T4__MEAS_LAP", 1000, "latency_mean_ms") < base / 100
    assert mean(rows, "S_Proposed_V1_T4__MEAS__range800", 1000, "latency_mean_ms") > base
    assert mean(rows, "S_Proposed_V1_T4__MEAS__adv0p1", 1000, "latency_mean_ms") > mean(rows, "S_Proposed_V1_T4__MEAS__adv0p0", 1000, "latency_mean_ms")
    # a hash-only scheme is insensitive to the adversary share
    assert abs(mean(rows, "S_Dhillon_Karla__MEAS__adv0p1", 1000, "latency_mean_ms") - mean(rows, "S_Dhillon_Karla__MEAS__adv0p0", 1000, "latency_mean_ms")) < 0.1


def test_jiang_latency_is_set_by_t_c_not_by_the_unverified_split():
    rows = load()
    lo = [mean(rows, f"S_JIANG_published__MEAS__Tc0p32__devshare{s}", 1000, "latency_mean_ms") for s in ("0p0", "0p5", "1p0")]
    hi = [mean(rows, f"S_JIANG_published__MEAS__Tc32p4__devshare{s}", 100, "latency_mean_ms") for s in ("0p0", "0p5", "1p0")]
    assert max(lo) - min(lo) < 0.1 and min(hi) > 50 * max(lo)
    # the split matters for server busy time, which is the number the guess controls
    b = [mean(rows, f"S_JIANG_published__MEAS__Tc0p32__devshare{s}", 1000, "server_busy_total_ms") for s in ("0p0", "0p5", "1p0")]
    assert b[0] > b[1] > b[2]


def test_bits_and_energy_scale_with_session_size():
    rows = load()
    k1, k2 = mean(rows, "M_Proposed_V1_T4__BASE", 1000, "kbit_on_air"), mean(rows, "M_Proposed_V1_text__BASE", 1000, "kbit_on_air")
    assert k2 < k1 / 3
    e1, e2 = mean(rows, "M_Proposed_V1_T4__BASE", 1000, "energy_mJ"), mean(rows, "M_Proposed_V1_text__BASE", 1000, "energy_mJ")
    assert abs(e1 / e2 - k1 / k2) < 1e-6 * k1 / k2 + 0.01
