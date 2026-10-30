"""Independent reference vectors for the Section III protocol (issue #2).

This script deliberately imports nothing from `hybrid_ecc_auth`. It restates the
protocol from the written specification in README.md (this directory) using only
the standard library (hashlib, hmac, json, base64) and a direct AES-256-GCM call
with a caller-chosen IV. HKDF is written out from RFC 5869 rather than taken from
a library wrapper.

Every primitive is checked against published known-answer vectors before any
protocol vector is produced, so a wrong helper fails here and not silently.

    python generate_reference_vectors.py            # rewrite the JSON files
    python generate_reference_vectors.py --check    # fail if they are out of date
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HERE = Path(__file__).resolve().parent
JSON_PATH = HERE / "reference_vectors.json"
TXT_PATH = HERE / "reference_vectors.txt"

# NIST P-256 group order n (FIPS 186-4); lambda_X lives in Z*_n.
P256_N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551

INFO_ROOT = b"hybrid-ecc-auth/pairwise-root/v1"
INFO_SESSION = b"hybrid-ecc-auth/session-key/v1"

MASTER_SECRET = b"reference-vector-master-secret"
DEVICE_ID = "device-001"
SERVER_ID = "server-A"

# (name, epoch t, N_i, N_j, IV of M1, IV of M2). All values are fixed on purpose.
CASES = [
    (
        "epoch0",
        0,
        bytes.fromhex("000102030405060708090a0b0c0d0e0f"),
        bytes.fromhex("f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"),
        bytes.fromhex("a0a1a2a3a4a5a6a7a8a9aaab"),
        bytes.fromhex("b0b1b2b3b4b5b6b7b8b9babb"),
    ),
    (
        "epoch3",
        3,
        bytes.fromhex("1112131415161718191a1b1c1d1e1f20"),
        bytes.fromhex("e1e2e3e4e5e6e7e8e9eaebecedeeef00"),
        bytes.fromhex("c0c1c2c3c4c5c6c7c8c9cacb"),
        bytes.fromhex("d0d1d2d3d4d5d6d7d8d9dadb"),
    ),
]


# ---------------------------------------------------------------- primitives
def sha256(*parts: bytes) -> bytes:
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.digest()


def hkdf_sha256(ikm: bytes, info: bytes, length: int, salt: bytes = b"") -> bytes:
    """RFC 5869. An empty salt means HashLen zero bytes (section 2.2)."""
    prk = hmac.new(salt or bytes(32), ikm, hashlib.sha256).digest()
    okm, block, counter = b"", b"", 1
    while len(okm) < length:
        block = hmac.new(prk, block + info + bytes([counter]), hashlib.sha256).digest()
        okm += block
        counter += 1
    return okm[:length]


def gcm_encrypt(key: bytes, iv: bytes, plaintext: bytes, aad: bytes) -> tuple[bytes, bytes]:
    combined = AESGCM(key).encrypt(iv, plaintext, aad)
    return combined[:-16], combined[-16:]


def u64(x: int) -> bytes:
    return x.to_bytes(8, "big")


def b64(x: bytes) -> str:
    return base64.b64encode(x).decode("ascii")


def known_answer_checks() -> None:
    """RFC 5869 A.1 and A.3, NIST SP 800-38D / McGrew-Viega test case 16, FIPS 180."""
    assert sha256(b"abc").hex() == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

    ikm = bytes.fromhex("0b" * 22)
    okm1 = hkdf_sha256(
        ikm,
        bytes.fromhex("f0f1f2f3f4f5f6f7f8f9"),
        42,
        salt=bytes.fromhex("000102030405060708090a0b0c"),
    )
    assert okm1.hex() == (
        "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
        "34007208d5b887185865"
    )
    okm3 = hkdf_sha256(ikm, b"", 42)
    assert okm3.hex() == (
        "8da4e775a563c18f715f802a063c5a31b8a11f5c5ee1879ec3454e5f3c738d2d"
        "9d201395faa4b61a96c8"
    )

    key = bytes.fromhex("feffe9928665731c6d6a8f9467308308" * 2)
    iv = bytes.fromhex("cafebabefacedbaddecaf888")
    pt = bytes.fromhex(
        "d9313225f88406e5a55909c5aff5269a86a7a9531534f7da2e4c303d8a318a72"
        "1c3c0c95956809532fcf0e2449a6b525b16aedf5aa0de657ba637b39"
    )
    aad = bytes.fromhex("feedfacedeadbeeffeedfacedeadbeefabaddad2")
    ct, tag = gcm_encrypt(key, iv, pt, aad)
    assert ct.hex() == (
        "522dc1f099567d07f47f37a32a84427d643a8cdcbfe5c0c97598a2bd2555d1aa"
        "8cb08e48590dbb3da7b08b1056828838c5f61e6393ba7a0abcc9f662"
    )
    assert tag.hex() == "76fc6ece0f4e1768cddf8853bb2d551b"


# ----------------------------------------------------------------- protocol
def long_term_secret(identity: str) -> int:
    """Eq. 8: lambda_X = H1(ID_X || s) mod n, SHA-256, identity as UTF-8."""
    lam = int.from_bytes(sha256(identity.encode("utf-8"), MASTER_SECRET), "big") % P256_N
    return lam or 1


def build_case(name: str, t: int, n_i: bytes, n_j: bytes, iv1: bytes, iv2: bytes,
               lam_d: bytes, lam_s: bytes, k_star: bytes) -> dict:
    pid = sha256(lam_d, u64(t))                                  # Eq. 11

    m1_pt = pid + n_i + u64(t)                                   # Eq. 13 plaintext
    m1_ct, m1_tag = gcm_encrypt(k_star, iv1, m1_pt, b"")         # Eq. 13/14, no AAD
    m1_wire = json.dumps(
        {"v": 1, "type": "M1", "pid": b64(pid), "nonce": b64(iv1), "ct": b64(m1_ct), "tag": b64(m1_tag)},
        separators=(",", ":"),
    )

    m2_pt = n_j + u64(t)                                         # Eq. 17 plaintext
    m2_aad = pid + n_i                                           # binds M1 into sigma_2
    m2_ct, m2_tag = gcm_encrypt(k_star, iv2, m2_pt, m2_aad)
    m2_wire = json.dumps(
        {"v": 1, "type": "M2", "sid": SERVER_ID, "nonce": b64(iv2), "ct": b64(m2_ct), "tag": b64(m2_tag)},
        separators=(",", ":"),
    )
    envelope = json.dumps({"ok": True, "payload": m2_wire})      # demo transport envelope

    session_key = hkdf_sha256(k_star + n_i + n_j + u64(t), INFO_SESSION, 32)  # Eq. 16

    return {
        "name": name,
        "epoch": t,
        "n_i": n_i.hex(), "n_j": n_j.hex(), "iv_m1": iv1.hex(), "iv_m2": iv2.hex(),
        "pid": pid.hex(),
        "m1_plaintext": m1_pt.hex(), "m1_ciphertext": m1_ct.hex(), "m1_tag": m1_tag.hex(),
        "m1_wire": m1_wire,
        "m2_plaintext": m2_pt.hex(), "m2_aad": m2_aad.hex(),
        "m2_ciphertext": m2_ct.hex(), "m2_tag": m2_tag.hex(),
        "m2_wire": m2_wire,
        "envelope": envelope,
        "session_key": session_key.hex(),
    }


def build() -> dict:
    known_answer_checks()
    lam_d = long_term_secret(DEVICE_ID).to_bytes(32, "big")
    lam_s = long_term_secret(SERVER_ID).to_bytes(32, "big")
    k_star = hkdf_sha256(lam_d + lam_s, INFO_ROOT, 32)           # Eq. 9, device lambda first
    return {
        "description": "Independent reference vectors; see README.md for the specification.",
        "master_secret": MASTER_SECRET.decode("ascii"),
        "device_id": DEVICE_ID,
        "server_id": SERVER_ID,
        "lambda_device": lam_d.hex(),
        "lambda_server": lam_s.hex(),
        "pairwise_root": k_star.hex(),
        "cases": [build_case(*c, lam_d=lam_d, lam_s=lam_s, k_star=k_star) for c in CASES],
    }


def flat_text(doc: dict) -> str:
    """name=value lines, so the C test can read the vectors without a JSON parser."""
    lines = [f"{k}={doc[k]}" for k in ("device_id", "server_id", "lambda_device", "lambda_server", "pairwise_root")]
    for case in doc["cases"]:
        p = case["name"]
        for k, v in case.items():
            if k != "name":
                lines.append(f"{p}.{k}={v}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify committed files are current")
    args = ap.parse_args()

    doc = build()
    js = json.dumps(doc, indent=2) + "\n"
    txt = flat_text(doc)
    if args.check:
        ok = JSON_PATH.read_text() == js and TXT_PATH.read_text() == txt
        print("reference vectors are current" if ok else "reference vectors are OUT OF DATE")
        return 0 if ok else 1
    JSON_PATH.write_text(js)
    TXT_PATH.write_text(txt)
    print(f"wrote {JSON_PATH.name} and {TXT_PATH.name} ({len(doc['cases'])} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
