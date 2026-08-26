"""Unit tests for protocol/login_gate.py (FR-6)."""

from __future__ import annotations

from hybrid_ecc_auth.protocol.login_gate import LoginGate, compute_login_hash


def test_compute_login_hash_deterministic():
    h1 = compute_login_hash(b"AA:BB:CC:DD:EE:FF", b"correct horse")
    h2 = compute_login_hash(b"AA:BB:CC:DD:EE:FF", b"correct horse")
    assert h1 == h2
    assert len(h1) == 32


def test_compute_login_hash_sensitive_to_mac_and_password():
    base = compute_login_hash(b"mac-1", b"pwd")
    assert base != compute_login_hash(b"mac-2", b"pwd")
    assert base != compute_login_hash(b"mac-1", b"other-pwd")


def test_login_gate_disabled_by_default():
    gate = LoginGate()
    assert gate.enabled is False


def test_login_gate_accepts_correct_password():
    gate = LoginGate(enabled=True)
    req = gate.build_request(b"mac-1", b"correct-password")
    assert gate.verify(req, expected_password=b"correct-password") is True


def test_login_gate_rejects_wrong_password():
    gate = LoginGate(enabled=True)
    req = gate.build_request(b"mac-1", b"correct-password")
    assert gate.verify(req, expected_password=b"wrong-password") is False


def test_login_gate_rejects_tampered_mac_binding():
    gate = LoginGate(enabled=True)
    req = gate.build_request(b"mac-1", b"pwd")
    tampered = type(req)(mac_address=b"mac-2", login_hash=req.login_hash)
    assert gate.verify(tampered, expected_password=b"pwd") is False
