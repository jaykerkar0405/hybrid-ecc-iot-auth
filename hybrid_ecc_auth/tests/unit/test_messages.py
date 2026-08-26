"""Unit tests for protocol/messages.py (wire-format serialization)."""

from __future__ import annotations

import pytest

from hybrid_ecc_auth.protocol.messages import (
    Message1,
    Message2,
    MessageFormatError,
    PROTOCOL_VERSION,
)


def test_message1_round_trip():
    msg = Message1(pid=b"\x01" * 32, gcm_nonce=b"\x02" * 12, ciphertext=b"\x03" * 20, tag=b"\x04" * 16)
    restored = Message1.from_bytes(msg.to_bytes())
    assert restored == msg


def test_message2_round_trip():
    msg = Message2(server_id="server-A", gcm_nonce=b"\x05" * 12, ciphertext=b"\x06" * 20, tag=b"\x07" * 16)
    restored = Message2.from_bytes(msg.to_bytes())
    assert restored == msg


def test_message1_rejects_wrong_type():
    msg2_bytes = Message2(server_id="x", gcm_nonce=b"\x00" * 12, ciphertext=b"", tag=b"\x00" * 16).to_bytes()
    with pytest.raises(MessageFormatError):
        Message1.from_bytes(msg2_bytes)


def test_message2_rejects_wrong_type():
    msg1_bytes = Message1(pid=b"\x00" * 32, gcm_nonce=b"\x00" * 12, ciphertext=b"", tag=b"\x00" * 16).to_bytes()
    with pytest.raises(MessageFormatError):
        Message2.from_bytes(msg1_bytes)


def test_rejects_malformed_json():
    with pytest.raises(MessageFormatError):
        Message1.from_bytes(b"not json at all")


def test_rejects_wrong_protocol_version():
    import base64
    import json

    payload = {
        "v": PROTOCOL_VERSION + 1,
        "type": "M1",
        "pid": base64.b64encode(b"\x00" * 32).decode(),
        "nonce": base64.b64encode(b"\x00" * 12).decode(),
        "ct": base64.b64encode(b"").decode(),
        "tag": base64.b64encode(b"\x00" * 16).decode(),
    }
    with pytest.raises(MessageFormatError):
        Message1.from_bytes(json.dumps(payload).encode())


def test_message1_is_pure_json_ascii_bytes():
    msg = Message1(pid=b"\xff" * 32, gcm_nonce=b"\x00" * 12, ciphertext=b"\xaa" * 5, tag=b"\xbb" * 16)
    raw = msg.to_bytes()
    raw.decode("ascii")  # must not raise -- base64 keeps it ASCII-safe
