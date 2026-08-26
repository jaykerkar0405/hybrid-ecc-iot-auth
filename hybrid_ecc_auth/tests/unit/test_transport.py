"""Unit tests for demo/_transport.py (Section 4.3 framing + envelope)."""

from __future__ import annotations

import socket

import pytest

from hybrid_ecc_auth.demo import _transport


def test_send_and_recv_frame_round_trip():
    a, b = socket.socketpair()
    try:
        payload = b'{"hello": "world"}'
        _transport.send_frame(a, payload)
        assert _transport.recv_frame(b) == payload
    finally:
        a.close()
        b.close()


def test_send_frame_rejects_oversized_payload():
    a, b = socket.socketpair()
    try:
        with pytest.raises(ValueError):
            _transport.send_frame(a, b"x" * (_transport.MAX_FRAME_BYTES + 1))
    finally:
        a.close()
        b.close()


def test_recv_frame_raises_on_peer_close_mid_frame():
    a, b = socket.socketpair()
    try:
        # Announce a frame longer than what we actually send, then close.
        import struct

        a.sendall(struct.pack(">I", 100))
        a.sendall(b"short")
        a.close()
        with pytest.raises(ConnectionError):
            _transport.recv_frame(b)
    finally:
        b.close()


def test_ok_envelope_round_trip():
    envelope_bytes = _transport.build_ok_envelope(b'{"type":"M2"}')
    parsed = _transport.parse_envelope(envelope_bytes)
    assert parsed["ok"] is True
    assert parsed["payload"] == '{"type":"M2"}'


def test_error_envelope_round_trip():
    envelope_bytes = _transport.build_error_envelope("ReplayDetected", "stale epoch 0")
    parsed = _transport.parse_envelope(envelope_bytes)
    assert parsed["ok"] is False
    assert parsed["error_type"] == "ReplayDetected"
    assert parsed["message"] == "stale epoch 0"
