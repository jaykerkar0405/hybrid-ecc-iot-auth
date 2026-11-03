"""Pseudonym-resolution strategies (protocol/resolution.py): every strategy
must authenticate honest devices through the full Section III exchange,
reject replays, and spend exactly the probes its closed form predicts."""

from __future__ import annotations

import os

import pytest

from hybrid_ecc_auth.protocol.device import Device
from hybrid_ecc_auth.protocol.errors import ReplayDetected, UnknownPeerError
from hybrid_ecc_auth.protocol.messages import Message1
from hybrid_ecc_auth.protocol.resolution import (
    ClockScan,
    ClockTable,
    CounterTable,
    LinearScan,
    TimeMemoryTable,
)
from hybrid_ecc_auth.protocol.server import Server
from hybrid_ecc_auth.protocol.ta import TrustedAuthority

SERVER = "srv"
LOOKBACK, FORWARD = 16, 8


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def fleet(n: int, resolver, *, epoch_clock=None):
    ta = TrustedAuthority(master_secret=b"resolution-tests")
    manifest = [{"identity": f"dev-{i:04d}", "role": "device"} for i in range(n)] + [
        {"identity": SERVER, "role": "server"}
    ]
    creds = ta.enroll_batch(manifest)
    srv = creds[SERVER]
    srv.peer_secrets = {f"dev-{i:04d}": creds[f"dev-{i:04d}"].lam for i in range(n)}
    devices = []
    for i in range(n):
        c = creds[f"dev-{i:04d}"]
        c.peer_secrets[SERVER] = srv.lam
        devices.append(Device(c, epoch_clock=epoch_clock))
    return devices, Server(srv, resolver=resolver)


def handshake(device: Device, server: Server) -> None:
    result = server.handle_auth_request(device.build_auth_request(SERVER))
    device.complete_auth(result.response_bytes)


def forged_m1(template: bytes) -> bytes:
    m = Message1.from_bytes(template)
    return Message1(pid=os.urandom(32), gcm_nonce=m.gcm_nonce, ciphertext=m.ciphertext, tag=m.tag).to_bytes()


# -- O1: the original linear scan -------------------------------------------------------------------------------

def test_linear_scan_is_the_default_and_matches_closed_form():
    n = 12
    devices, server = fleet(n, None)
    assert isinstance(server.resolver, LinearScan)
    log = server.session_log
    for round_ in range(LOOKBACK + 2):
        for i, d in enumerate(devices):
            before = sum(len(log.epoch_search_window(e.credential.identity)) for e in devices[:i])
            last = log._last_accepted_epoch.get(d.credential.identity, -1)
            lo = max(0, last - LOOKBACK)
            server.resolver.reset_counters()
            handshake(d, server)
            assert server.resolver.probes == before + (last + 1 - lo) + 1
    # steady state (last >= L): window of L + F + 1 = 25 epochs, target at index L + 1
    for i, d in enumerate(devices):
        server.resolver.reset_counters()
        handshake(d, server)
        assert server.resolver.probes == i * (LOOKBACK + FORWARD + 1) + (LOOKBACK + 2)
    server.resolver.reset_counters()
    with pytest.raises(UnknownPeerError):
        server.handle_auth_request(forged_m1(devices[0].build_auth_request(SERVER)))
    assert server.resolver.probes == n * (LOOKBACK + FORWARD + 1)


# -- O2: counter epochs with a precomputed table -----------------------------------------------------------------

def test_counter_table_costs_one_probe_per_authentication_and_none_per_forgery():
    n = 20
    devices, server = fleet(n, CounterTable())
    assert server.resolver.precompute_probes == n * FORWARD
    for _ in range(3):
        for d in devices:
            server.resolver.reset_counters()
            handshake(d, server)
            assert server.resolver.probes == 1
    server.resolver.reset_counters()
    with pytest.raises(UnknownPeerError):
        server.handle_auth_request(forged_m1(devices[0].build_auth_request(SERVER)))
    assert server.resolver.probes == 0
    assert len(server.resolver._table) == n * FORWARD


def test_counter_table_rejects_replay():
    devices, server = fleet(3, CounterTable())
    m1 = devices[1].build_auth_request(SERVER)
    server.handle_auth_request(m1)
    with pytest.raises(UnknownPeerError):
        server.handle_auth_request(m1)


# -- O3 / O4: clock epochs ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("kind", [ClockScan, ClockTable])
def test_clock_epochs_authenticate_and_reject_nonce_replay(kind):
    clock = Clock()
    devices, server = fleet(6, kind(clock, epoch_seconds=60), epoch_clock=lambda: int(clock() // 60))
    for d in devices:
        handshake(d, server)
    m1 = devices[2].build_auth_request(SERVER)
    server.handle_auth_request(m1)
    with pytest.raises(ReplayDetected):
        server.handle_auth_request(m1)
    clock.now = 125.0  # two epochs later
    for d in devices:
        handshake(d, server)


def test_clock_epochs_make_sessions_in_one_epoch_linkable():
    clock = Clock()
    devices, _ = fleet(1, ClockScan(clock), epoch_clock=lambda: int(clock() // 60))
    a = Message1.from_bytes(devices[0].build_auth_request(SERVER)).pid
    b = Message1.from_bytes(devices[0].build_auth_request(SERVER)).pid
    assert a == b
    clock.now = 60.0
    assert Message1.from_bytes(devices[0].build_auth_request(SERVER)).pid != a


def test_clock_scan_probe_counts():
    n, drift = 10, 1
    clock = Clock()
    clock.now = 600.0
    devices, server = fleet(n, ClockScan(clock, drift=drift), epoch_clock=lambda: int(clock() // 60))
    w = 2 * drift + 1
    for i, d in enumerate(devices):
        server.resolver.reset_counters()
        handshake(d, server)
        assert server.resolver.probes == i * w + 1
    server.resolver.reset_counters()
    with pytest.raises(UnknownPeerError):
        server.handle_auth_request(forged_m1(devices[0].build_auth_request(SERVER)))
    assert server.resolver.probes == n * w


def test_clock_table_costs_n_probes_per_epoch_and_none_per_authentication():
    n, drift = 15, 1
    clock = Clock()
    clock.now = 600.0
    devices, server = fleet(n, ClockTable(clock, drift=drift), epoch_clock=lambda: int(clock() // 60))
    assert server.resolver.precompute_probes == n * (2 * drift + 1)
    server.resolver.reset_counters()
    for d in devices:
        handshake(d, server)
    assert server.resolver.probes == 0 and server.resolver.precompute_probes == 0
    clock.now = 660.0
    handshake(devices[0], server)
    assert server.resolver.precompute_probes == n


# -- Rainbow time-memory trade-off --------------------------------------------------------------------------------

def test_time_memory_table_resolves_and_rejects_replay():
    devices, server = fleet(40, TimeMemoryTable(lifetime=32))
    r = server.resolver
    assert r.coverage() > 0.99
    ok = 0
    for _ in range(3):
        for d in devices:
            try:
                handshake(d, server)
                ok += 1
            except UnknownPeerError:
                pass  # an uncovered point: the device's next attempt uses the next epoch
    assert ok >= 0.97 * 3 * len(devices)
    d = devices[0]
    m1 = d.build_auth_request(SERVER)
    try:
        server.handle_auth_request(m1)
    except UnknownPeerError:
        pytest.skip("point not covered")
    with pytest.raises(ReplayDetected):
        server.handle_auth_request(m1)


def test_time_memory_table_survives_many_dropped_messages():
    devices, server = fleet(10, TimeMemoryTable(lifetime=64))
    d = devices[3]
    for _ in range(20):
        d.build_auth_request(SERVER)  # dropped by the adversary
    results = []
    for _ in range(3):
        try:
            handshake(d, server)
            results.append("ok")
        except UnknownPeerError:
            results.append("miss")
    assert "ok" in results


# -- Desynchronisation under dropped M1 (R9) ----------------------------------------------------------------------

@pytest.mark.parametrize("make", [lambda: None, CounterTable])
def test_counter_epochs_lock_out_after_forward_tolerance_drops(make):
    for drops, expect_ok in ((FORWARD - 1, True), (FORWARD, False)):
        devices, server = fleet(2, make())
        d = devices[0]
        handshake(d, server)
        for _ in range(drops):
            d.build_auth_request(SERVER)
        if expect_ok:
            handshake(d, server)
        else:
            with pytest.raises(UnknownPeerError):
                handshake(d, server)
