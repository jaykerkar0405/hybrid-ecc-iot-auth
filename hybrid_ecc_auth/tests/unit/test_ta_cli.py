"""Unit tests for demo/ta_cli.py (FR-2.4 batch enrollment CLI)."""

from __future__ import annotations

import json

from hybrid_ecc_auth.demo.ta_cli import main
from hybrid_ecc_auth.storage.keystore import KeyStore


def _write_manifest(tmp_path, entries):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(entries))
    return path


def test_enroll_writes_bundle_per_entity_and_master_secret(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        [
            {"identity": "device-001", "role": "device"},
            {"identity": "server-A", "role": "server"},
        ],
    )
    out_dir = tmp_path / "creds"

    try:
        main(["enroll", "--manifest", str(manifest), "--out-dir", str(out_dir)])
    except SystemExit as exc:
        assert exc.code == 0

    assert (out_dir / "device-001.json").exists()
    assert (out_dir / "server-A.json").exists()
    assert (out_dir / "ta_master_secret.hex").exists()

    device_cred = KeyStore(out_dir / "device-001.json").load()
    server_cred = KeyStore(out_dir / "server-A.json").load()
    assert device_cred.peer_secrets == {"server-A": server_cred.lam}
    assert server_cred.peer_secrets == {"device-001": device_cred.lam}


def test_enroll_reuses_master_secret_across_invocations(tmp_path):
    out_dir = tmp_path / "creds"
    manifest1 = _write_manifest(tmp_path, [{"identity": "device-001", "role": "device"}])

    try:
        main(["enroll", "--manifest", str(manifest1), "--out-dir", str(out_dir)])
    except SystemExit as exc:
        assert exc.code == 0
    first_lam = KeyStore(out_dir / "device-001.json").load().lam

    manifest2 = _write_manifest(tmp_path, [{"identity": "device-001", "role": "device"}])
    try:
        main(["enroll", "--manifest", str(manifest2), "--out-dir", str(out_dir)])
    except SystemExit as exc:
        assert exc.code == 0
    second_lam = KeyStore(out_dir / "device-001.json").load().lam

    assert first_lam == second_lam  # same master secret -> deterministic lambda (Eq. 8)


def test_enroll_rejects_non_device_credential_role_mismatch(tmp_path, capsys):
    manifest = _write_manifest(tmp_path, [{"identity": "device-001", "role": "bogus-role"}])
    out_dir = tmp_path / "creds"
    try:
        main(["enroll", "--manifest", str(manifest), "--out-dir", str(out_dir)])
        raised = False
    except SystemExit as exc:
        raised = True
        assert exc.code != 0
    assert raised
