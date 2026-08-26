"""Section 4.3: local TCP sockets with length-prefixed framed JSON.

The protocol core (protocol/messages.py) has no transport dependency and
already produces self-contained JSON blobs (binary fields base64-encoded).
This module adds only what a raw TCP byte stream needs on top of that: a
4-byte big-endian length prefix per frame, plus a thin success/error
envelope so a server can signal *why* it rejected a request (SEC-0x)
instead of just closing the connection.
"""

from __future__ import annotations

import json
import socket
import struct

_LENGTH_PREFIX_FORMAT = ">I"
_LENGTH_PREFIX_SIZE = struct.calcsize(_LENGTH_PREFIX_FORMAT)
MAX_FRAME_BYTES = 1 << 20  # 1 MiB -- generous upper bound for a demo message


def send_frame(sock: socket.socket, payload: bytes) -> None:
    if len(payload) > MAX_FRAME_BYTES:
        raise ValueError(f"frame of {len(payload)} bytes exceeds MAX_FRAME_BYTES={MAX_FRAME_BYTES}")
    sock.sendall(struct.pack(_LENGTH_PREFIX_FORMAT, len(payload)) + payload)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("peer closed the connection mid-frame")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_frame(sock: socket.socket) -> bytes:
    (length,) = struct.unpack(_LENGTH_PREFIX_FORMAT, _recv_exact(sock, _LENGTH_PREFIX_SIZE))
    if length > MAX_FRAME_BYTES:
        raise ValueError(f"peer announced a frame of {length} bytes, exceeding MAX_FRAME_BYTES={MAX_FRAME_BYTES}")
    return _recv_exact(sock, length)


def build_ok_envelope(payload_bytes: bytes) -> bytes:
    return json.dumps({"ok": True, "payload": payload_bytes.decode("ascii")}).encode("ascii")


def build_error_envelope(error_type: str, message: str) -> bytes:
    return json.dumps({"ok": False, "error_type": error_type, "message": message}).encode("ascii")


def parse_envelope(data: bytes) -> dict:
    return json.loads(data.decode("ascii"))
