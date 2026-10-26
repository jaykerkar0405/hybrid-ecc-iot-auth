"""Step 4: deterministic cost model."""
import math
import refmodel as M
import step4_common_env as S4
from common import T3, T4


def test_base_table_v_under_table_iii_matches_audit():
    t = M.const_A(17.3)
    assert abs(M.scheme_costs(M.PROPOSED["V1 Table V as printed"], t)[3] - 23.68) < 1e-9
    tot = lambda n: M.scheme_costs(M.base_printed()[n], t)[4]
    assert abs(tot("Turkanovic [12]") - 6.08) < 1e-9
    assert abs(tot("Dhillon-Karla [13]") - 7.04) < 1e-9 and abs(tot("Jiang [15]") - 7.04) < 1e-9


def test_corrected_turkanovic_same_total_different_split():
    t = M.const_A(17.3)
    a = M.scheme_costs(M.base_printed()["Turkanovic [12]"], t)
    b = M.scheme_costs(M.turkanovic_corrected(), t)
    assert abs(a[4] - b[4]) < 1e-12 and a[1] != b[1] and a[2] != b[2]


def test_jiang_published_cost():
    j = M.scheme_costs(M.jiang_published(), {"H": 0.2, "C": 32.4})
    assert abs(j[3] - (11 * 0.2 + 6 * 32.4)) < 1e-9
    assert abs(M.scheme_costs(M.jiang_published(), {"H": 0.32, "C": 0.32})[3] - 17 * 0.32) < 1e-9


def test_tc_crossover_is_exact():
    t = M.const_C(80)
    p = M.scheme_costs(M.PROPOSED["V2 Table V + session KDF"], t)[3]
    jp = M.jiang_published()["total"]
    tc_star = (p - jp["H"] * t["H"]) / jp["C"]
    t2 = dict(t); t2["C"] = tc_star
    assert math.isclose(M.scheme_costs(M.jiang_published(), t2)[3], p, rel_tol=1e-12)


def test_measured_constants_match_audit_numbers():
    t = M.const_C(80, "aes_big")
    assert abs(t["H"] - 0.036342) < 1e-9 and abs(t["ECM"] - 276.35) < 1e-9
    assert abs(M.measured_kdf_ratio(80) - 17.31) < 0.01


def test_reductions_reproduce_ours_comm_numbers():
    comp = {k: v[4] for k, v in T4.items() if not k.startswith("Proposed")}
    r = M.reductions(comp, 1024)
    assert round(r["vs best"], 1) == 36.0 and round(r["vs mean"], 1) == 57.5


def test_model_is_deterministic():
    a = M.scheme_costs(M.PROPOSED["V3 Eq.22 with AEAD"], M.const_C(160))
    b = M.scheme_costs(M.PROPOSED["V3 Eq.22 with AEAD"], M.const_C(160))
    assert a == b
    assert S4.all_schemes().keys() == S4.all_schemes().keys()


def test_rank_of():
    assert M.rank_of(5, {"a": 1, "b": 9, "c": None}) == (2, 1)
