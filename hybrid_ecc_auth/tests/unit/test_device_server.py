"""Unit/integration tests for protocol/device.py + protocol/server.py
(FR-5: two-message mutual authentication)."""

from __future__ import annotations

import time

import pytest

from hybrid_ecc_auth.protocol.device import Device
from hybrid_ecc_auth.protocol.errors import (
    BlockedEntity,
    CoverageError,
    IntegrityError,
    SessionTimeoutError,
    UnknownPeerError,
)
from hybrid_ecc_auth.protocol.messages import Message1, Message2
from hybrid_ecc_auth.protocol.server import Server
from hybrid_ecc_auth.protocol.ta import TrustedAuthority


def _provision(n_devices: int = 1, n_servers: int = 1):
    ta = TrustedAuthority(master_secret=b"integration-test-secret")
    devices = [ta.enroll(f"device-{i:03d}", "device") for i in range(n_devices)]
    servers = [ta.enroll(f"server-{chr(65 + i)}", "server") for i in range(n_servers)]
    ta.share_mutual_peer_keys(devices + servers)
    return ta, devices, servers


def test_successful_mutual_authentication_end_to_end():
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred)

    msg1 = device.build_auth_request("server-A")
    result = server.handle_auth_request(msg1)
    session_key_device = device.complete_auth(result.response_bytes)

    assert session_key_device == result.session_key
    assert len(session_key_device) == 32
    assert result.peer_identity == "device-000"


def test_repeated_sessions_use_fresh_nonces_and_keys():
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred)

    keys = []
    for _ in range(3):
        msg1 = device.build_auth_request("server-A")
        result = server.handle_auth_request(msg1)
        device.complete_auth(result.response_bytes)
        keys.append(result.session_key)

    assert len(set(keys)) == 3  # SEC-07: no key reuse across sessions


def test_server_rejects_unknown_device():
    """Device knows the server's peer key (one-directional share), but the
    server was never given the device's peer key -- it cannot resolve the
    incoming pseudonym at all."""
    ta = TrustedAuthority(master_secret=b"s")
    known_device = ta.enroll("device-known", "device")
    server_cred = ta.enroll("server-B", "server")
    ta.share_peer_keys(known_device, [server_cred])

    device = Device(known_device)
    server = Server(server_cred)
    msg1 = device.build_auth_request("server-B")
    with pytest.raises(UnknownPeerError):
        server.handle_auth_request(msg1)


def test_server_rejects_tampered_ciphertext_sec03():
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred)

    msg1_bytes = device.build_auth_request("server-A")
    msg1 = Message1.from_bytes(msg1_bytes)
    tampered = Message1(
        pid=msg1.pid,
        gcm_nonce=msg1.gcm_nonce,
        ciphertext=bytes([msg1.ciphertext[0] ^ 0x01]) + msg1.ciphertext[1:],
        tag=msg1.tag,
    )
    with pytest.raises(IntegrityError):
        server.handle_auth_request(tampered.to_bytes())


def test_device_rejects_tampered_response():
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred)

    msg1 = device.build_auth_request("server-A")
    result = server.handle_auth_request(msg1)
    msg2 = Message2.from_bytes(result.response_bytes)
    tampered = Message2(
        server_id=msg2.server_id,
        gcm_nonce=msg2.gcm_nonce,
        ciphertext=msg2.ciphertext,
        tag=bytes([msg2.tag[0] ^ 0x01]) + msg2.tag[1:],
    )
    with pytest.raises(IntegrityError):
        device.complete_auth(tampered.to_bytes())


def test_device_rejects_unsolicited_response():
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred)

    msg1 = device.build_auth_request("server-A")
    result = server.handle_auth_request(msg1)
    device.complete_auth(result.response_bytes)  # consumes the pending session

    with pytest.raises(UnknownPeerError):
        device.complete_auth(result.response_bytes)  # replayed onto an already-completed device


def test_coverage_gate_blocks_out_of_range_device():
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred, coverage_predicate=lambda peer: False)
    with pytest.raises(CoverageError):
        device.build_auth_request("server-A")


def test_server_coverage_gate_rejects_regardless_of_crypto_validity():
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred, coverage_predicate=lambda peer: False)

    msg1 = device.build_auth_request("server-A")
    with pytest.raises(CoverageError):
        server.handle_auth_request(msg1)


def test_session_timeout_raises_and_counts_as_failure():
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred, session_timeout=0.01)
    server = Server(server_cred)

    msg1 = device.build_auth_request("server-A")
    result = server.handle_auth_request(msg1)
    time.sleep(0.05)
    with pytest.raises(SessionTimeoutError):
        device.complete_auth(result.response_bytes)


def test_block_list_after_max_attempts_short_circuits_pre_crypto():
    _ta, [device_cred], [server_cred] = _provision()
    device = Device(device_cred)
    server = Server(server_cred, max_attempts=3)

    for _ in range(3):
        msg1_bytes = device.build_auth_request("server-A")
        msg1 = Message1.from_bytes(msg1_bytes)
        tampered = Message1(pid=msg1.pid, gcm_nonce=msg1.gcm_nonce, ciphertext=b"\x00" * len(msg1.ciphertext), tag=msg1.tag)
        with pytest.raises(IntegrityError):
            server.handle_auth_request(tampered.to_bytes())

    assert server.session_log.is_blocked("device-000")

    msg1_bytes = device.build_auth_request("server-A")
    with pytest.raises(BlockedEntity):
        server.handle_auth_request(msg1_bytes)


def test_block_list_broadcast_pubsub_hook():
    _ta, [device_cred], [server_cred] = _provision()
    server = Server(server_cred)
    notified = []
    server.session_log.subscribe_block(notified.append)
    server.session_log.block("device-000")
    assert notified == ["device-000"]
