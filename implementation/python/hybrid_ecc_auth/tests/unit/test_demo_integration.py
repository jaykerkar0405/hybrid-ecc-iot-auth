"""End-to-end demo integration test over a real loopback TCP socket:
exercises demo/_transport.py + demo/server_node.py's connection handler
together with real Device/Server protocol objects (acceptance criteria 1
and 2: a successful run, and a visibly-rejected replay)."""

from __future__ import annotations

import socket
import threading

from hybrid_ecc_auth.demo import _transport
from hybrid_ecc_auth.demo.server_node import _handle_connection
from hybrid_ecc_auth.protocol.device import Device
from hybrid_ecc_auth.protocol.server import Server
from hybrid_ecc_auth.protocol.ta import TrustedAuthority


def _start_server(server: Server, n_connections: int) -> tuple[socket.socket, threading.Thread]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))  # ephemeral port
    listener.listen(5)

    def _serve():
        for _ in range(n_connections):
            conn, addr = listener.accept()
            _handle_connection(conn, addr, server)

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    return listener, thread


def _send_and_receive(port: int, request_bytes: bytes) -> dict:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        _transport.send_frame(sock, request_bytes)
        response_bytes = _transport.recv_frame(sock)
    return _transport.parse_envelope(response_bytes)


def test_demo_end_to_end_success_and_replay_rejection():
    ta = TrustedAuthority(master_secret=b"demo-integration-secret")
    device_cred = ta.enroll("demo-device", "device")
    server_cred = ta.enroll("demo-server", "server")
    ta.share_mutual_peer_keys([device_cred, server_cred])

    device = Device(device_cred)
    server = Server(server_cred)

    listener, thread = _start_server(server, n_connections=2)
    try:
        port = listener.getsockname()[1]

        # 1. A legitimate, fresh request succeeds end-to-end.
        msg1_bytes = device.build_auth_request("demo-server")
        envelope = _send_and_receive(port, msg1_bytes)
        assert envelope["ok"] is True
        msg2_bytes = envelope["payload"].encode("ascii")
        session_key = device.complete_auth(msg2_bytes)
        assert len(session_key) == 32

        # 2. Replaying the exact same M1 is visibly, correctly rejected --
        # not a crash, not a silent success (acceptance criterion 2).
        envelope2 = _send_and_receive(port, msg1_bytes)
        assert envelope2["ok"] is False
        assert envelope2["error_type"] == "ReplayDetected"
    finally:
        listener.close()
        thread.join(timeout=2)
