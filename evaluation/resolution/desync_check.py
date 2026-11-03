# Copyright (c) 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur
# SPDX-License-Identifier: Apache-2.0
"""Check how the per-peer epoch counter behaves when M1 messages are dropped
or the device restarts.

The base paper's threat model lets the adversary drop messages (Sec. III-M).
Our implementation advances the device epoch when it builds M1
(`Device.build_auth_request`) and the server only searches epochs
`last-16 .. last+8` (`SessionLog.epoch_search_window`). This script measures
what that combination does. It describes OUR epoch choice (see
docs/conformance.md, assumption register), not the paper's protocol.

Run from the repository root:
    python -I evaluation/resolution/desync_check.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "implementation/python"))

from hybrid_ecc_auth.protocol.device import Device  # noqa: E402
from hybrid_ecc_auth.protocol.server import Server  # noqa: E402
from hybrid_ecc_auth.protocol.ta import TrustedAuthority  # noqa: E402

SERVER_ID = "server-A"


def _provision():
    ta = TrustedAuthority(master_secret=os.urandom(32))
    device_cred = ta.enroll("device-000", "device")
    server_cred = ta.enroll(SERVER_ID, "server")
    ta.share_mutual_peer_keys([device_cred, server_cred])
    return device_cred, server_cred


def _handshake(device: Device, server: Server) -> str:
    try:
        result = server.handle_auth_request(device.build_auth_request(SERVER_ID))
        device.complete_auth(result.response_bytes)
        return "ok"
    except Exception as exc:  # report the rejection type, do not hide it
        return type(exc).__name__


def dropped_m1(drops: int, prior_success: bool) -> list[str]:
    device_cred, server_cred = _provision()
    device, server = Device(device_cred), Server(server_cred)
    if prior_success:
        assert _handshake(device, server) == "ok"
    for _ in range(drops):
        device.build_auth_request(SERVER_ID)  # the adversary drops this M1
    return [_handshake(device, server) for _ in range(3)]


def device_restart() -> str:
    device_cred, server_cred = _provision()
    server = Server(server_cred)
    device = Device(device_cred)
    for _ in range(3):
        assert _handshake(device, server) == "ok"
    restarted = Device(device_cred)  # epoch counter is in RAM and restarts at 0
    return _handshake(restarted, server)


def main() -> None:
    print("drops  prior_success  next three honest handshakes")
    for prior in (False, True):
        for drops in (6, 7, 8, 9, 12):
            print(f"{drops:5d}  {str(prior):13s}  {dropped_m1(drops, prior)}")
    print(f"device restart after 3 successful handshakes: {device_restart()}")


if __name__ == "__main__":
    main()
