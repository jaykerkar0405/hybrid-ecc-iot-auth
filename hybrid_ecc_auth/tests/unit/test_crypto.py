"""Unit tests for hybrid_ecc_auth.crypto (FR-1)."""

from __future__ import annotations

import pytest
from cryptography.exceptions import InvalidTag

from hybrid_ecc_auth.crypto import aead, curve, hashes, kdf, nonce


# --- curve.py ----------------------------------------------------------


def test_reduce_mod_n_stays_in_range():
    for v in (0, 1, curve.CURVE_ORDER - 1, curve.CURVE_ORDER, curve.CURVE_ORDER + 5, 2**300):
        r = curve.reduce_mod_n(v)
        assert 1 <= r < curve.CURVE_ORDER


def test_reduce_mod_n_zero_maps_to_one():
    assert curve.reduce_mod_n(0) == 1
    assert curve.reduce_mod_n(curve.CURVE_ORDER) == 1


def test_scalar_to_public_point_deterministic_and_uncompressed():
    p1 = curve.scalar_to_public_point(12345)
    p2 = curve.scalar_to_public_point(12345)
    assert p1 == p2
    assert p1[0] == 0x04  # uncompressed SEC1 point prefix
    assert len(p1) == 65  # 1 + 32 + 32 for P-256


def test_scalar_to_public_point_differs_for_different_scalars():
    assert curve.scalar_to_public_point(1) != curve.scalar_to_public_point(2)


# --- hashes.py -----------------------------------------------------------


def test_h1_derive_secret_deterministic_and_in_range():
    lam1 = hashes.h1_derive_secret(b"device-001", b"master-secret")
    lam2 = hashes.h1_derive_secret(b"device-001", b"master-secret")
    assert lam1 == lam2
    assert 1 <= lam1 < curve.CURVE_ORDER


def test_h1_derive_secret_differs_per_identity():
    lam_a = hashes.h1_derive_secret(b"device-001", b"master-secret")
    lam_b = hashes.h1_derive_secret(b"device-002", b"master-secret")
    assert lam_a != lam_b


def test_h2_pseudonym_deterministic_per_epoch():
    pid1 = hashes.h2_pseudonym(42, 7)
    pid2 = hashes.h2_pseudonym(42, 7)
    assert pid1 == pid2
    assert len(pid1) == 32


def test_h2_pseudonym_rotates_with_epoch():
    pid_t0 = hashes.h2_pseudonym(42, 0)
    pid_t1 = hashes.h2_pseudonym(42, 1)
    assert pid_t0 != pid_t1


def test_h3_rekey_binder_deterministic():
    assert hashes.h3_rekey_binder(3) == hashes.h3_rekey_binder(3)
    assert hashes.h3_rekey_binder(3) != hashes.h3_rekey_binder(4)


# --- kdf.py ----------------------------------------------------------------


def test_kdf_deterministic_given_same_inputs():
    k1 = kdf.kdf(b"ikm-material", info=b"info-a")
    k2 = kdf.kdf(b"ikm-material", info=b"info-a")
    assert k1 == k2
    assert len(k1) == 32


def test_kdf_differs_by_info_and_ikm():
    base = kdf.kdf(b"ikm", info=b"a")
    assert base != kdf.kdf(b"ikm", info=b"b")
    assert base != kdf.kdf(b"other-ikm", info=b"a")


def test_kdf_variable_length():
    assert len(kdf.kdf(b"x", length=16)) == 16
    assert len(kdf.kdf(b"x", length=64)) == 64


# --- aead.py ---------------------------------------------------------------


def test_aead_roundtrip():
    key = b"\x11" * aead.KEY_LEN
    plaintext = b"hello IoT device"
    n, ct, tag = aead.encrypt(key, plaintext, aad=b"context")
    pt = aead.decrypt(key, n, ct, tag, aad=b"context")
    assert pt == plaintext
    assert len(n) == aead.GCM_NONCE_LEN
    assert len(tag) == aead.TAG_LEN


def test_aead_tamper_ciphertext_rejected():
    key = b"\x22" * aead.KEY_LEN
    n, ct, tag = aead.encrypt(key, b"payload")
    tampered = bytes([ct[0] ^ 0x01]) + ct[1:]
    with pytest.raises(InvalidTag):
        aead.decrypt(key, n, tampered, tag)


def test_aead_tamper_tag_rejected():
    key = b"\x33" * aead.KEY_LEN
    n, ct, tag = aead.encrypt(key, b"payload")
    tampered_tag = bytes([tag[0] ^ 0x01]) + tag[1:]
    with pytest.raises(InvalidTag):
        aead.decrypt(key, n, ct, tampered_tag)


def test_aead_wrong_aad_rejected():
    key = b"\x44" * aead.KEY_LEN
    n, ct, tag = aead.encrypt(key, b"payload", aad=b"correct")
    with pytest.raises(InvalidTag):
        aead.decrypt(key, n, ct, tag, aad=b"wrong")


def test_aead_rejects_bad_key_length():
    with pytest.raises(ValueError):
        aead.encrypt(b"short-key", b"payload")


def test_aead_nonces_are_random():
    key = b"\x55" * aead.KEY_LEN
    n1, _, _ = aead.encrypt(key, b"same plaintext")
    n2, _, _ = aead.encrypt(key, b"same plaintext")
    assert n1 != n2


# --- nonce.py ----------------------------------------------------------


def test_generate_nonce_default_length():
    n = nonce.generate_nonce()
    assert len(n) == 16  # 128 bits


@pytest.mark.parametrize("bits,expected_bytes", [(128, 16), (192, 24), (256, 32)])
def test_generate_nonce_supported_lengths(bits, expected_bytes):
    assert len(nonce.generate_nonce(bits)) == expected_bytes


def test_generate_nonce_rejects_unsupported_length():
    with pytest.raises(ValueError):
        nonce.generate_nonce(100)


def test_generate_nonce_is_random():
    assert nonce.generate_nonce() != nonce.generate_nonce()
