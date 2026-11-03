"""hea-device: runnable device process (PRD Section 4.2, steps 3-4).

`authenticate` builds M1, sends it to a server, verifies M2, and on
success prints the derived session key's fingerprint (never the raw key)
and round-trip latency.

`authenticate --replay-last` deliberately resends the *exact* M1 bytes
from this device's most recent successful attempt (saved alongside its
credential bundle) to demonstrate the server's nonce/pseudonym freshness
check (SEC-01) rejecting it.
"""

from __future__ import annotations

import argparse
import hashlib
import socket
import sys
import time
from pathlib import Path

from ..protocol.device import Device
from ..protocol.errors import AuthenticationError
from ..protocol.messages import MessageFormatError
from ..storage.keystore import KeyStore
from . import _transport


def _last_msg1_path(credential_path: Path) -> Path:
    return credential_path.with_suffix(credential_path.suffix + ".last_m1")


def _parse_server_addr(value: str) -> tuple[str, int]:
    host, _, port = value.rpartition(":")
    if not host or not port.isdigit():
        raise argparse.ArgumentTypeError(f"--server-addr must be host:port, got {value!r}")
    return host, int(port)


def cmd_authenticate(args: argparse.Namespace) -> int:
    credential_path = Path(args.credential)
    credential = KeyStore(credential_path).load()
    if credential.role != "device":
        print(f"error: {credential_path} is a {credential.role!r} credential, not a device credential", file=sys.stderr)
        return 2

    device = Device(credential)
    host, port = _parse_server_addr(args.server_addr)
    last_msg1_path = _last_msg1_path(credential_path)

    if args.replay_last:
        if not last_msg1_path.exists():
            print(
                f"error: no captured M1 to replay yet -- run `hea-device authenticate` (without --replay-last) "
                f"at least once first, so it can save one to {last_msg1_path}",
                file=sys.stderr,
            )
            return 2
        msg1_bytes = last_msg1_path.read_bytes()
        print(f"[replay-demo] resending previously captured M1 ({len(msg1_bytes)} bytes) to {host}:{port} ...")
        built_fresh_request = False
    else:
        msg1_bytes = device.build_auth_request(args.server_id)
        last_msg1_path.write_bytes(msg1_bytes)
        built_fresh_request = True

    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=args.timeout) as sock:
            _transport.send_frame(sock, msg1_bytes)
            response_bytes = _transport.recv_frame(sock)
    except OSError as exc:
        print(f"error: could not reach server at {host}:{port}: {exc}", file=sys.stderr)
        return 1
    round_trip_ms = (time.perf_counter() - t0) * 1000.0

    envelope = _transport.parse_envelope(response_bytes)
    if not envelope["ok"]:
        print(
            f"REJECTED by server: {envelope['error_type']}: {envelope['message']} "
            f"(round-trip {round_trip_ms:.3f} ms)"
        )
        if args.replay_last:
            print("[replay-demo] rejection confirms the server's freshness check is working as intended.")
        return 1

    if not built_fresh_request:
        # We replayed an old M1 but the server (unexpectedly) accepted it --
        # there is no local pending session to complete it against.
        print(
            "warning: server unexpectedly accepted the replayed M1 -- cannot complete the handshake "
            "(no local session state for a replayed request). This indicates a freshness-check regression.",
            file=sys.stderr,
        )
        return 1

    msg2_bytes = envelope["payload"].encode("ascii")
    try:
        session_key = device.complete_auth(msg2_bytes)
    except (AuthenticationError, MessageFormatError) as exc:
        print(f"error verifying server response: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    fingerprint = hashlib.sha256(session_key).hexdigest()[:16]
    print(f"Mutual authentication succeeded with {args.server_id!r}.")
    print(f"  session key fingerprint: {fingerprint} (SHA-256[:16] of K_ij,t -- never the raw key)")
    print(f"  round-trip latency: {round_trip_ms:.3f} ms")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hea-device", description="Runnable device process (FR-5, device side).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth = subparsers.add_parser("authenticate", help="Authenticate to a server over TCP.")
    auth.add_argument("--credential", required=True, help="Path to this device's credential bundle (from hea-ta enroll).")
    auth.add_argument("--server-id", required=True, help="The server's TA-issued identity (e.g. server-A).")
    auth.add_argument("--server-addr", required=True, help="host:port of the running hea-server process.")
    auth.add_argument("--timeout", type=float, default=5.0, help="Socket connect/recv timeout in seconds.")
    auth.add_argument(
        "--replay-last",
        action="store_true",
        help="Adversary demo mode: resend the last captured M1 instead of building a fresh one (SEC-01).",
    )
    auth.set_defaults(func=cmd_authenticate)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
