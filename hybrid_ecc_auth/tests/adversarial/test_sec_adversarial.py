"""Required adversarial test cases (PRD Section 7.2, SEC-01..SEC-08).

The adversary model (PRD Section 7.1 / paper Section III-M) is a PPT
attacker that fully controls the channel -- eavesdrop, replay, drop,
reorder, inject -- but cannot compromise the offline TA phase or extract
lambda_X without physical/implementation-level compromise.
"""

from __future__ import annotations

import os

import pytest

from hybrid_ecc_auth.crypto.aead import GCM_NONCE_LEN
from hybrid_ecc_auth.crypto.hashes import h2_pseudonym
from hybrid_ecc_auth.protocol.device import Device
from hybrid_ecc_auth.protocol.errors import (
    BlockedEntity,
    CoverageError,
    IntegrityError,
    ReplayDetected,
)
from hybrid_ecc_auth.protocol.messages import Message1
from hybrid_ecc_auth.protocol.server import Server
from hybrid_ecc_auth.protocol.ta import TrustedAuthority


def _provision(n_devices: int = 1, n_servers: int = 1):
    ta = TrustedAuthority(master_secret=os.urandom(32))
    devices = [ta.enroll(f"device-{i:03d}", "device") for i in range(n_devices)]
    servers = [ta.enroll(f"server-{chr(65 + i)}", "server") for i in range(n_servers)]
    ta.share_mutual_peer_keys(devices + servers)
    return ta, devices, servers


# --- SEC-01 --------------------------------------------------------------


def test_sec01_replay_captured_valid_m1_is_rejected():
    """Replay a previously captured, valid M1 -> Rejected: stale
    nonce/pseudonym epoch detected."""
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred)

    msg1_bytes = device.build_auth_request("server-A")
    server.handle_auth_request(msg1_bytes)  # legitimate first use, succeeds

    with pytest.raises(ReplayDetected):
        server.handle_auth_request(msg1_bytes)  # attacker replays the exact same M1


# --- SEC-02 ----------------------------------------------------------------


def test_sec02_replay_captured_valid_m2_to_different_device_session_is_rejected():
    """Replay a previously captured, valid M2 to a different device
    session -> Rejected: sigma_2/nonce binding mismatch."""
    _ta, [device1_cred, device2_cred], [server_cred] = _provision(n_devices=2)
    device1 = Device(device1_cred)
    device2 = Device(device2_cred)
    server = Server(server_cred)

    msg1_from_device1 = device1.build_auth_request("server-A")
    result1 = server.handle_auth_request(msg1_from_device1)

    # device2 also has an outstanding session with the same server...
    device2.build_auth_request("server-A")
    # ...but the attacker delivers device1's captured, valid M2 to device2 instead.
    with pytest.raises(IntegrityError):
        device2.complete_auth(result1.response_bytes)


# --- SEC-03 ----------------------------------------------------------------


@pytest.mark.parametrize("field", ["ciphertext", "tag"])
def test_sec03_bit_flip_in_c1_or_mu1_is_rejected(field):
    """Flip a single bit in C1 or mu_1 in transit -> Rejected: AEAD tag /
    MAC verification failure."""
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred)

    msg1 = Message1.from_bytes(device.build_auth_request("server-A"))
    kwargs = {
        "pid": msg1.pid,
        "gcm_nonce": msg1.gcm_nonce,
        "ciphertext": msg1.ciphertext,
        "tag": msg1.tag,
    }
    original = bytearray(kwargs[field])
    original[0] ^= 0x01
    kwargs[field] = bytes(original)
    tampered = Message1(**kwargs)

    with pytest.raises(IntegrityError):
        server.handle_auth_request(tampered.to_bytes())


# --- SEC-04 ----------------------------------------------------------------


def test_sec04_forged_m1_without_lambda_for_known_pid_is_rejected():
    """Attacker without lambda_Vi attempts to forge M1 for a known PID ->
    Rejected: cannot produce valid mu_1."""
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred)

    # Attacker observes (or predicts) the device's current, legitimate
    # pseudonym, but has no access to lambda_device / k*_ij, so it cannot
    # produce a valid ciphertext or tag -- it can only guess random bytes.
    known_pid = device.current_pseudonym("server-A")
    forged = Message1(
        pid=known_pid,
        gcm_nonce=os.urandom(GCM_NONCE_LEN),
        ciphertext=os.urandom(72),
        tag=os.urandom(16),
    )

    with pytest.raises(IntegrityError):
        server.handle_auth_request(forged.to_bytes())


# --- SEC-05 ----------------------------------------------------------------


def test_sec05_three_failed_attempts_blocks_entity_fourth_short_circuits():
    """3 consecutive failed attempts from same identity -> Entity is
    block-listed; 4th attempt short-circuited pre-crypto."""
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred, max_attempts=3)

    for _ in range(3):
        msg1 = Message1.from_bytes(device.build_auth_request("server-A"))
        forged = Message1(pid=msg1.pid, gcm_nonce=msg1.gcm_nonce, ciphertext=os.urandom(len(msg1.ciphertext)), tag=msg1.tag)
        with pytest.raises(IntegrityError):
            server.handle_auth_request(forged.to_bytes())

    assert server.session_log.is_blocked("device-000")

    # The 4th attempt must be rejected *before* any AEAD decrypt call --
    # verified indirectly: even a perfectly well-formed, fresh, valid M1 is
    # rejected purely on block-list membership.
    msg1_valid = device.build_auth_request("server-A")
    with pytest.raises(BlockedEntity):
        server.handle_auth_request(msg1_valid)


# --- SEC-06 ------------------------------------------------------------


def test_sec06_pseudonym_unlinkability_smoke_test():
    """Two devices' pseudonyms compared across epochs by a passive
    observer -> statistical indistinguishability check (unlinkability
    smoke test, not a formal proof)."""
    ta = TrustedAuthority(master_secret=os.urandom(32))
    device_a = ta.enroll("device-a", "device")
    device_b = ta.enroll("device-b", "device")

    n_epochs = 200
    pids_a = [h2_pseudonym(device_a.lam, t) for t in range(n_epochs)]
    pids_b = [h2_pseudonym(device_b.lam, t) for t in range(n_epochs)]

    # (1) No exact collisions within or across devices -- a trivial
    # linkability break would show up as a repeated pseudonym.
    assert len(set(pids_a)) == n_epochs
    assert len(set(pids_b)) == n_epochs
    assert set(pids_a).isdisjoint(pids_b)

    def mean_hamming_distance_bits(seq_x, seq_y) -> float:
        distances = []
        for x, y in zip(seq_x, seq_y):
            distances.append(bin(int.from_bytes(x, "big") ^ int.from_bytes(y, "big")).count("1"))
        return sum(distances) / len(distances)

    # (2) A passive observer comparing device A's own pseudonym stream
    # across consecutive epochs sees the same ~128-bit average Hamming
    # distance (out of 256 bits) as comparing two *different* devices'
    # streams -- i.e. "same device, next epoch" is statistically
    # indistinguishable from "unrelated device" by this simple metric.
    same_device_consecutive = mean_hamming_distance_bits(pids_a[:-1], pids_a[1:])
    cross_device = mean_hamming_distance_bits(pids_a, pids_b)

    expected = 128.0  # half of 256 output bits, for an ideal hash
    tolerance = 20.0  # generous smoke-test bound, not a rigorous statistical test
    assert abs(same_device_consecutive - expected) < tolerance
    assert abs(cross_device - expected) < tolerance


# --- SEC-07 ------------------------------------------------------------


def test_sec07_session_keys_differ_across_independent_honest_runs():
    """Session key comparison across two independent honest runs -> Keys
    differ (freshness / no key reuse across sessions)."""
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred)

    keys = []
    for _ in range(5):
        msg1 = device.build_auth_request("server-A")
        result = server.handle_auth_request(msg1)
        device.complete_auth(result.response_bytes)
        keys.append(result.session_key)

    assert len(set(keys)) == len(keys)


# --- SEC-08 ------------------------------------------------------------


def test_sec08_out_of_range_device_rejected_at_allow_gate_regardless_of_crypto_validity():
    """Out-of-range device (coverage predicate = False) attempts
    authentication -> Rejected at Allow_ij(t) gate regardless of crypto
    validity."""
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)  # device itself has no coverage restriction
    server = Server(server_cred, coverage_predicate=lambda peer: False)  # server sees it as out of range

    # The device produces a perfectly valid M1 -- the crypto is not at fault.
    msg1 = device.build_auth_request("server-A")
    with pytest.raises(CoverageError):
        server.handle_auth_request(msg1)
