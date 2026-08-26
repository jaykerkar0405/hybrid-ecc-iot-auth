"""Unit tests for protocol/entity.py (FR-3, FR-7)."""

from __future__ import annotations

import pytest

from hybrid_ecc_auth.protocol.entity import (
    Entity,
    derive_pairwise_root,
    derive_session_key,
)
from hybrid_ecc_auth.protocol.ta import TrustedAuthority


def _make_pair():
    ta = TrustedAuthority(master_secret=b"s")
    device = ta.enroll("device-001", "device")
    server = ta.enroll("server-A", "server")
    ta.share_mutual_peer_keys([device, server])
    return device, server


def test_derive_pairwise_root_symmetric_regardless_of_caller():
    device_cred, server_cred = _make_pair()
    device_entity = Entity(device_cred)
    server_entity = Entity(server_cred)

    root_from_device = device_entity.get_pairwise_root("server-A")
    root_from_server = server_entity.get_pairwise_root("device-001")
    assert root_from_device == root_from_server
    assert len(root_from_device) == 32


def test_derive_pairwise_root_matches_manual_eq9():
    device_cred, server_cred = _make_pair()
    expected = derive_pairwise_root(device_cred.lam, server_cred.lam)
    assert Entity(device_cred).get_pairwise_root("server-A") == expected


def test_get_pairwise_root_raises_for_unknown_peer():
    device_cred, _server_cred = _make_pair()
    entity = Entity(device_cred)
    with pytest.raises(KeyError):
        entity.get_pairwise_root("no-such-peer")


def test_pairwise_root_is_cached():
    device_cred, _server_cred = _make_pair()
    entity = Entity(device_cred)
    root1 = entity.get_pairwise_root("server-A")
    # Mutate the peer secret post-hoc; a cached value should not change.
    device_cred.peer_secrets["server-A"] = 999999
    root2 = entity.get_pairwise_root("server-A")
    assert root1 == root2


def test_invalidate_pairwise_root_single_and_all():
    device_cred, _server_cred = _make_pair()
    entity = Entity(device_cred)
    entity.get_pairwise_root("server-A")
    assert "server-A" in entity._pairwise_root_cache

    entity.invalidate_pairwise_root("server-A")
    assert "server-A" not in entity._pairwise_root_cache

    entity.get_pairwise_root("server-A")
    entity.invalidate_pairwise_root()
    assert entity._pairwise_root_cache == {}


def test_derive_session_key_deterministic_and_sensitive_to_all_inputs():
    k_star = b"\x01" * 32
    ni, nj = b"\x02" * 16, b"\x03" * 16
    k1 = derive_session_key(k_star, ni, nj, 5)
    k2 = derive_session_key(k_star, ni, nj, 5)
    assert k1 == k2
    assert len(k1) == 32

    assert derive_session_key(k_star, ni, nj, 6) != k1
    assert derive_session_key(k_star, b"\x04" * 16, nj, 5) != k1
    assert derive_session_key(k_star, ni, b"\x05" * 16, 5) != k1


def test_coverage_predicate_defaults_true():
    device_cred, _ = _make_pair()
    entity = Entity(device_cred)
    assert entity.coverage_ok("server-A") is True
    assert entity.access_control_gate("server-A", auth_ok=True) is True
    assert entity.access_control_gate("server-A", auth_ok=False) is False


def test_coverage_predicate_pluggable_out_of_range():
    device_cred, _ = _make_pair()
    entity = Entity(device_cred, coverage_predicate=lambda peer: False)
    assert entity.coverage_ok("server-A") is False
    # Even a valid auth cannot pass the gate if coverage fails (SEC-08).
    assert entity.access_control_gate("server-A", auth_ok=True) is False
