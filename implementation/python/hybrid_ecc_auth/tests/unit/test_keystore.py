"""Unit tests for storage/keystore.py (demo-grade credential storage)."""

from __future__ import annotations

import stat

from hybrid_ecc_auth.protocol.ta import TrustedAuthority
from hybrid_ecc_auth.storage.keystore import KeyStore


def test_save_and_load_round_trip(tmp_path):
    ta = TrustedAuthority(master_secret=b"keystore-test")
    cred = ta.enroll("device-001", "device", export_public_point=True)
    other = ta.enroll("server-A", "server")
    ta.share_peer_keys(cred, [other])

    path = tmp_path / "device-001.json"
    store = KeyStore(path)
    assert store.exists() is False
    store.save(cred)
    assert store.exists() is True

    restored = store.load()
    assert restored.identity == cred.identity
    assert restored.lam == cred.lam
    assert restored.public_point == cred.public_point
    assert restored.peer_secrets == cred.peer_secrets


def test_save_sets_restrictive_permissions(tmp_path):
    ta = TrustedAuthority(master_secret=b"perm-test")
    cred = ta.enroll("device-001", "device")
    path = tmp_path / "sub" / "device-001.json"
    KeyStore(path).save(cred)

    mode = path.stat().st_mode
    assert not (mode & stat.S_IRWXG)
    assert not (mode & stat.S_IRWXO)
    assert mode & stat.S_IRUSR and mode & stat.S_IWUSR


def test_load_tightens_overly_permissive_file(tmp_path):
    ta = TrustedAuthority(master_secret=b"perm-test-2")
    cred = ta.enroll("device-001", "device")
    path = tmp_path / "device-001.json"
    store = KeyStore(path)
    store.save(cred)

    path.chmod(0o644)  # simulate a world-readable file (e.g. restored from an archive)
    store.load()
    mode = path.stat().st_mode
    assert not (mode & stat.S_IRWXG)
    assert not (mode & stat.S_IRWXO)
