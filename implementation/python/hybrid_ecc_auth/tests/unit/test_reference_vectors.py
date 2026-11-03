"""Conformance of the Python implementation to the independent reference vectors.

The expected values come from tests/vectors/generate_reference_vectors.py, which
shares no code with the implementation. The real Device and Server are driven
with the vectors' fixed protocol nonces and GCM IVs and must reproduce every
byte, then reject tampered and replayed messages.
"""

from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path

import pytest

from hybrid_ecc_auth.crypto import aead
from hybrid_ecc_auth.protocol import device as device_mod
from hybrid_ecc_auth.protocol import server as server_mod
from hybrid_ecc_auth.protocol.device import Device
from hybrid_ecc_auth.protocol.errors import IntegrityError, ReplayDetected, UnknownPeerError
from hybrid_ecc_auth.protocol.server import Server
from hybrid_ecc_auth.protocol.ta import TrustedAuthority

VECTOR_DIR = Path(__file__).resolve().parent.parent / "vectors"
DOC = json.loads((VECTOR_DIR / "reference_vectors.json").read_text())
CASES = {c["name"]: c for c in DOC["cases"]}


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_reference_vectors", VECTOR_DIR / "generate_reference_vectors.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parties():
    ta = TrustedAuthority(master_secret=DOC["master_secret"].encode("ascii"))
    dev = ta.enroll(DOC["device_id"], "device")
    srv = ta.enroll(DOC["server_id"], "server")
    ta.share_mutual_peer_keys([dev, srv])
    return dev, srv


@pytest.fixture
def fixed_randomness(monkeypatch):
    """Queue the vector's N_i/N_j (protocol nonces) and IVs (GCM) for the next handshake."""

    def install(case):
        nonces = [bytes.fromhex(case["n_i"]), bytes.fromhex(case["n_j"])]
        ivs = [bytes.fromhex(case["iv_m1"]), bytes.fromhex(case["iv_m2"])]

        def next_iv(n):
            assert n == 12, "only GCM IVs are drawn from os.urandom in this flow"
            return ivs.pop(0)

        # N_i is drawn by the device first and N_j by the server second.
        monkeypatch.setattr(device_mod, "generate_nonce", lambda bits=128: nonces.pop(0))
        monkeypatch.setattr(server_mod, "generate_nonce", lambda bits=128: nonces.pop(0))
        monkeypatch.setattr(aead.os, "urandom", next_iv)

    return install


def _handshake(case, fixed_randomness):
    dev_cred, srv_cred = _parties()
    device, server = Device(dev_cred), Server(srv_cred)
    if case["epoch"]:
        device._epoch[DOC["server_id"]] = case["epoch"]
    fixed_randomness(case)
    return device, server


def test_generator_self_checks_pass_and_files_are_current():
    gen = _load_generator()
    gen.known_answer_checks()
    assert json.dumps(gen.build(), indent=2) + "\n" == (VECTOR_DIR / "reference_vectors.json").read_text()


def test_long_term_secrets_and_pairwise_root_match_vectors():
    dev_cred, srv_cred = _parties()
    assert dev_cred.lam.to_bytes(32, "big").hex() == DOC["lambda_device"]
    assert srv_cred.lam.to_bytes(32, "big").hex() == DOC["lambda_server"]
    assert Device(dev_cred).get_pairwise_root(DOC["server_id"]).hex() == DOC["pairwise_root"]
    assert Server(srv_cred).get_pairwise_root(DOC["device_id"]).hex() == DOC["pairwise_root"]


@pytest.mark.parametrize("name", sorted(CASES))
def test_handshake_reproduces_every_vector_byte(name, fixed_randomness):
    case = CASES[name]
    device, server = _handshake(case, fixed_randomness)

    assert device.current_pseudonym(DOC["server_id"], case["epoch"]).hex() == case["pid"]

    m1 = device.build_auth_request(DOC["server_id"])
    assert m1.decode("utf-8") == case["m1_wire"]

    result = server.handle_auth_request(m1)
    envelope_payload = result.response_bytes.decode("ascii")
    assert envelope_payload == case["m2_wire"]
    assert result.session_key.hex() == case["session_key"]

    assert device.complete_auth(result.response_bytes).hex() == case["session_key"]


@pytest.mark.parametrize("name", sorted(CASES))
def test_independent_decryption_of_wire_messages_yields_vector_plaintext(name):
    """Decrypt the vector wire bytes with a bare AESGCM call, no project code."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    case = CASES[name]
    key = bytes.fromhex(DOC["pairwise_root"])
    m1 = json.loads(case["m1_wire"])
    m2 = json.loads(case["m2_wire"])
    d = base64.b64decode
    assert AESGCM(key).decrypt(d(m1["nonce"]), d(m1["ct"]) + d(m1["tag"]), None).hex() == case["m1_plaintext"]
    assert AESGCM(key).decrypt(d(m2["nonce"]), d(m2["ct"]) + d(m2["tag"]), bytes.fromhex(case["m2_aad"])).hex() == case["m2_plaintext"]


def _flip(b64_text: str, index: int = 0) -> str:
    raw = bytearray(base64.b64decode(b64_text))
    raw[index] ^= 0x01
    return base64.b64encode(bytes(raw)).decode("ascii")


@pytest.mark.parametrize("field", ["nonce", "ct", "tag"])
def test_server_rejects_tampered_m1_fields(field, fixed_randomness):
    case = CASES["epoch0"]
    device, server = _handshake(case, fixed_randomness)
    m1 = json.loads(device.build_auth_request(DOC["server_id"]))
    m1[field] = _flip(m1[field])
    with pytest.raises(IntegrityError):
        server.handle_auth_request(json.dumps(m1, separators=(",", ":")).encode())


def test_server_does_not_resolve_a_tampered_pseudonym(fixed_randomness):
    case = CASES["epoch0"]
    device, server = _handshake(case, fixed_randomness)
    m1 = json.loads(device.build_auth_request(DOC["server_id"]))
    m1["pid"] = _flip(m1["pid"])
    with pytest.raises(UnknownPeerError):
        server.handle_auth_request(json.dumps(m1, separators=(",", ":")).encode())


@pytest.mark.parametrize("field", ["nonce", "ct", "tag"])
def test_device_rejects_tampered_m2_fields(field, fixed_randomness):
    case = CASES["epoch0"]
    device, server = _handshake(case, fixed_randomness)
    result = server.handle_auth_request(device.build_auth_request(DOC["server_id"]))
    m2 = json.loads(result.response_bytes)
    m2[field] = _flip(m2[field])
    with pytest.raises(IntegrityError):
        device.complete_auth(json.dumps(m2, separators=(",", ":")).encode())


def test_replayed_m1_is_rejected(fixed_randomness):
    case = CASES["epoch0"]
    device, server = _handshake(case, fixed_randomness)
    m1 = device.build_auth_request(DOC["server_id"])
    server.handle_auth_request(m1)
    with pytest.raises(ReplayDetected):
        server.handle_auth_request(m1)


def test_m2_from_another_session_is_rejected(fixed_randomness):
    """sigma_2 binds PID||N_i: a valid M2 for the epoch0 vector must fail in a later session."""
    dev_cred, srv_cred = _parties()
    device = Device(dev_cred)
    stale_m2 = CASES["epoch0"]["m2_wire"].encode("ascii")

    # A fresh request (different N_i) is outstanding; the old M2 does not match its AAD.
    device.build_auth_request(DOC["server_id"])
    with pytest.raises(IntegrityError):
        device.complete_auth(stale_m2)
