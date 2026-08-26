"""Unit tests for protocol/ta.py (FR-2)."""

from __future__ import annotations

import socket

import pytest

from hybrid_ecc_auth.protocol.ta import Credential, TrustedAuthority


def test_enroll_is_deterministic_given_same_master_secret():
    ta1 = TrustedAuthority(master_secret=b"fixed-secret")
    ta2 = TrustedAuthority(master_secret=b"fixed-secret")
    cred1 = ta1.enroll("device-001", "device")
    cred2 = ta2.enroll("device-001", "device")
    assert cred1.lam == cred2.lam


def test_enroll_differs_per_identity_and_role_rejects_bad_role():
    ta = TrustedAuthority(master_secret=b"s")
    device = ta.enroll("device-001", "device")
    server = ta.enroll("server-A", "server")
    assert device.lam != server.lam
    with pytest.raises(ValueError):
        ta.enroll("bogus", "router")


def test_enroll_rejects_duplicate_identity():
    ta = TrustedAuthority(master_secret=b"s")
    ta.enroll("device-001", "device")
    with pytest.raises(ValueError):
        ta.enroll("device-001", "device")


def test_enroll_optional_public_point():
    ta = TrustedAuthority(master_secret=b"s")
    cred_no_point = ta.enroll("device-001", "device", export_public_point=False)
    cred_with_point = ta.enroll("device-002", "device", export_public_point=True)
    assert cred_no_point.public_point is None
    assert cred_with_point.public_point is not None
    assert len(cred_with_point.public_point) == 65


def test_enroll_batch():
    ta = TrustedAuthority(master_secret=b"s")
    manifest = [
        {"identity": "device-001", "role": "device"},
        {"identity": "device-002", "role": "device"},
        {"identity": "server-A", "role": "server", "export_public_point": True},
    ]
    creds = ta.enroll_batch(manifest)
    assert set(creds) == {"device-001", "device-002", "server-A"}
    assert creds["server-A"].public_point is not None


def test_share_peer_keys_populates_lambda_list_one_directional():
    ta = TrustedAuthority(master_secret=b"s")
    device = ta.enroll("device-001", "device")
    server = ta.enroll("server-A", "server")
    ta.share_peer_keys(device, [server])
    assert device.peer_secrets == {"server-A": server.lam}
    assert server.peer_secrets == {}  # not mutated


def test_share_mutual_peer_keys_full_mesh():
    ta = TrustedAuthority(master_secret=b"s")
    a = ta.enroll("device-001", "device")
    b = ta.enroll("device-002", "device")
    c = ta.enroll("server-A", "server")
    ta.share_mutual_peer_keys([a, b, c])
    assert a.peer_secrets == {"device-002": b.lam, "server-A": c.lam}
    assert b.peer_secrets == {"device-001": a.lam, "server-A": c.lam}
    assert c.peer_secrets == {"device-001": a.lam, "device-002": b.lam}


def test_lookup():
    ta = TrustedAuthority(master_secret=b"s")
    cred = ta.enroll("device-001", "device")
    assert ta.lookup("device-001") is cred
    with pytest.raises(KeyError):
        ta.lookup("nonexistent")


def test_credential_round_trip_serialization():
    ta = TrustedAuthority(master_secret=b"s")
    a = ta.enroll("device-001", "device", export_public_point=True)
    b = ta.enroll("server-A", "server")
    ta.share_peer_keys(a, [b])

    restored = Credential.from_dict(a.to_dict())
    assert restored.identity == a.identity
    assert restored.role == a.role
    assert restored.lam == a.lam
    assert restored.public_point == a.public_point
    assert restored.peer_secrets == a.peer_secrets


# --- FR-2.3: offline-only invariant -----------------------------------


def test_ta_operations_never_open_a_socket(monkeypatch):
    """Enforces FR-2.3: the offline registration path must not perform any
    network I/O. We monkeypatch socket.socket to explode if TA code ever
    tries to construct one."""

    def _forbidden(*args, **kwargs):
        raise AssertionError("TA registration attempted to open a network socket")

    monkeypatch.setattr(socket, "socket", _forbidden)

    ta = TrustedAuthority(master_secret=b"offline-only")
    a = ta.enroll("device-001", "device", export_public_point=True)
    b = ta.enroll("server-A", "server")
    ta.share_mutual_peer_keys([a, b])
    ta.enroll_batch([{"identity": "device-002", "role": "device"}])
    ta.lookup("device-001")
    Credential.from_dict(a.to_dict())
