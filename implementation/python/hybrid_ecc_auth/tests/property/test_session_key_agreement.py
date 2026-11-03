"""Correctness invariant (Eq. 20): Pr[K_{ij,t}^(V) = K_{ij,t}^(R)] = 1.

Non-functional requirement (PRD Section 8): verified in >= 10,000
randomized trials with zero failures, across multiple device/server pairs
and multiple simultaneous devices per server.
"""

from __future__ import annotations

import random

from hybrid_ecc_auth.protocol.device import Device
from hybrid_ecc_auth.protocol.server import Server
from hybrid_ecc_auth.protocol.ta import TrustedAuthority

TRIALS = 10_000


def test_session_key_agreement_holds_over_10000_trials():
    rng = random.Random(1234)
    ta = TrustedAuthority(master_secret=b"property-test-master-secret")

    n_devices, n_servers = 5, 2
    device_creds = [ta.enroll(f"device-{i:03d}", "device") for i in range(n_devices)]
    server_creds = [ta.enroll(f"server-{i:03d}", "server") for i in range(n_servers)]
    ta.share_mutual_peer_keys(device_creds + server_creds)

    devices = [Device(c) for c in device_creds]
    servers = {c.identity: Server(c) for c in server_creds}

    failures = 0
    for _ in range(TRIALS):
        device = rng.choice(devices)
        server_id = rng.choice(server_creds).identity
        server = servers[server_id]

        msg1 = device.build_auth_request(server_id)
        result = server.handle_auth_request(msg1)
        device_key = device.complete_auth(result.response_bytes)

        if device_key != result.session_key:
            failures += 1

    assert failures == 0, f"{failures}/{TRIALS} trials disagreed on the session key (Eq. 20 violated)"


def test_session_keys_are_uniformly_distinct_across_trials():
    """Sanity check that Eq. 16's inputs (fresh Ni, Nj per session) are
    actually doing their job -- no two sessions in a large batch should
    collide on the derived session key."""
    ta = TrustedAuthority(master_secret=b"distinctness-test-secret")
    device_cred = ta.enroll("device-000", "device")
    server_cred = ta.enroll("server-000", "server")
    ta.share_mutual_peer_keys([device_cred, server_cred])

    device = Device(device_cred)
    server = Server(server_cred)

    keys = set()
    for _ in range(2_000):
        msg1 = device.build_auth_request("server-000")
        result = server.handle_auth_request(msg1)
        device.complete_auth(result.response_bytes)
        keys.add(result.session_key)

    assert len(keys) == 2_000
