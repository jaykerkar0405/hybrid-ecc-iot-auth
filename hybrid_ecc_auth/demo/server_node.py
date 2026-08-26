"""hea-server: runnable server process (PRD Section 4.2, step 2).

Loads a credential bundle written by `hea-ta enroll` and listens for
framed authentication requests over TCP, handling them one connection at a
time (sufficient for a demo/reviewer walkthrough -- concurrency is not a
goal here).
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time

from ..protocol.errors import AuthenticationError
from ..protocol.messages import MessageFormatError
from ..protocol.server import Server
from ..storage.keystore import KeyStore
from . import _transport


def _log(event: dict) -> None:
    """Structured JSON logs, one per line. Never includes raw secret
    material (session keys, lambda, k*_ij) -- only outcome/latency/identity."""
    print(json.dumps(event), flush=True)


def _handle_connection(conn: socket.socket, addr, server: Server) -> None:
    with conn:
        try:
            request_bytes = _transport.recv_frame(conn)
        except (ConnectionError, ValueError) as exc:
            _log({"event": "auth_attempt", "outcome": "transport_error", "message": str(exc), "peer_addr": str(addr)})
            return

        t0 = time.perf_counter()
        try:
            result = server.handle_auth_request(request_bytes)
        except (AuthenticationError, MessageFormatError) as exc:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            _log(
                {
                    "event": "auth_attempt",
                    "outcome": "rejected",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                    "latency_ms": round(latency_ms, 4),
                    "peer_addr": str(addr),
                }
            )
            try:
                _transport.send_frame(conn, _transport.build_error_envelope(type(exc).__name__, str(exc)))
            except OSError:
                pass
            return

        latency_ms = (time.perf_counter() - t0) * 1000.0
        _log(
            {
                "event": "auth_attempt",
                "outcome": "accepted",
                "peer_identity": result.peer_identity,
                "latency_ms": round(latency_ms, 4),
                "peer_addr": str(addr),
            }
        )
        try:
            _transport.send_frame(conn, _transport.build_ok_envelope(result.response_bytes))
        except OSError as exc:
            _log({"event": "auth_attempt", "outcome": "response_send_failed", "message": str(exc), "peer_addr": str(addr)})


def cmd_start(args: argparse.Namespace) -> int:
    credential = KeyStore(args.credential).load()
    if credential.role != "server":
        print(f"error: {args.credential} is a {credential.role!r} credential, not a server credential", file=sys.stderr)
        return 2

    server = Server(credential)
    _log(
        {
            "event": "server_start",
            "identity": credential.identity,
            "host": args.host,
            "port": args.port,
            "known_peers": sorted(credential.peer_secrets),
        }
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((args.host, args.port))
        listener.listen(args.backlog)
        try:
            while True:
                conn, addr = listener.accept()
                _handle_connection(conn, addr, server)
        except KeyboardInterrupt:
            _log({"event": "server_stop", "reason": "keyboard_interrupt"})
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hea-server", description="Runnable server process (FR-5, server side).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Load a credential bundle and listen for authentication requests.")
    start.add_argument("--credential", required=True, help="Path to this server's credential bundle (from hea-ta enroll).")
    start.add_argument("--host", default="127.0.0.1")
    start.add_argument("--port", type=int, default=8443)
    start.add_argument("--backlog", type=int, default=5)
    start.set_defaults(func=cmd_start)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
