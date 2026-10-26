"""Step 5: seeded SimPy model."""
import step5_netsim as N

DEV, _ = N.platform("esp8266_80mhz.csv")
SRV, TP = N.platform("esp8266_80mhz.csv")


def test_same_seed_same_result():
    a = N.run(200, "Proposed V1 (Table V)", 3, DEV, SRV, TP)
    b = N.run(200, "Proposed V1 (Table V)", 3, DEV, SRV, TP)
    assert a == b


def test_different_seed_differs():
    a = N.run(200, "Proposed V1 (Table V)", 1, DEV, SRV, TP)
    b = N.run(200, "Proposed V1 (Table V)", 2, DEV, SRV, TP)
    assert a != b


def test_hash_only_latency_independent_of_n():
    l1 = N.run(100, "Dhillon-Karla", 1, DEV, SRV, TP)["lat_mean_ms"]
    l2 = N.run(1000, "Dhillon-Karla", 1, DEV, SRV, TP)["lat_mean_ms"]
    assert abs(l1 - l2) / l1 < 0.05


def test_proposed_latency_grows_when_servers_resolve_all_reachable_devices():
    l1 = N.run(100, "Proposed V1 (Table V)", 1, DEV, SRV, TP)["lat_mean_ms"]
    l2 = N.run(1000, "Proposed V1 (Table V)", 1, DEV, SRV, TP)["lat_mean_ms"]
    assert l2 > 5 * l1


def test_nearest_only_policy_is_roughly_flat():
    l1 = N.run(100, "Proposed V1 (Table V)", 1, DEV, SRV, TP, policy="nearest")["lat_mean_ms"]
    l2 = N.run(1000, "Proposed V1 (Table V)", 1, DEV, SRV, TP, policy="nearest")["lat_mean_ms"]
    assert l2 < 3 * l1


def test_ecc_scheme_latency_dominated_by_device_scalar_mult():
    r = N.run(100, "Sadhukhan (ECC)", 1, DEV, SRV, TP)
    assert 270 < r["lat_mean_ms"] < 300


def test_server_count_is_five_percent_and_range_limits_reachability():
    r = N.run(100, "Dhillon-Karla", 1, DEV, SRV, TP, range_m=1.0)
    assert r["unreachable"] == 100
