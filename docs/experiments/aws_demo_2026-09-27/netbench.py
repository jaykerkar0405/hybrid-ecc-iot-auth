"""Networked benchmark for hybrid_ecc_auth between two hosts.

Modes:
  echo-server  --port P                 framed TCP echo (network baseline)
  echo         --addr H:P -n N --size B  framed echo RTT, new TCP conn per round
  auth         --credential C --server-id S --addr H:P -n N
               N sequential handshakes from ONE long-lived Device against a
               running hea-server; new TCP connection per handshake (same as
               the hea-device CLI). Times build_auth_request / network round
               trip / complete_auth separately.
  tamper       --credential C --server-id S --addr H:P -n N
               sends N M1s with one ciphertext bit flipped (SEC-02/SEC-05).
Writes JSON to --out.
"""

from __future__ import annotations

import argparse
import base64
import json
import resource
import socket
import statistics
import sys
import time

from hybrid_ecc_auth.demo import _transport


def addr(v):
    h, _, p = v.rpartition(":")
    return h, int(p)


def summarize(xs):
    xs = sorted(xs)
    n = len(xs)
    q = lambda p: xs[min(n - 1, int(round(p * (n - 1))))]
    return {
        "n": n,
        "mean": statistics.fmean(xs),
        "stdev": statistics.pstdev(xs),
        "min": xs[0],
        "p50": q(0.50),
        "p95": q(0.95),
        "p99": q(0.99),
        "max": xs[-1],
    }


def rss_kb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def echo_server(a):
    with socket.socket() as ls:
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ls.bind(("0.0.0.0", a.port))
        ls.listen(16)
        while True:
            c, _ = ls.accept()
            with c:
                try:
                    _transport.send_frame(c, _transport.recv_frame(c))
                except Exception:
                    pass


def echo(a):
    h, p = addr(a.addr)
    payload = b"x" * a.size
    rtts = []
    for i in range(a.warmup + a.n):
        t0 = time.perf_counter()
        with socket.create_connection((h, p), timeout=5) as s:
            _transport.send_frame(s, payload)
            _transport.recv_frame(s)
        dt = (time.perf_counter() - t0) * 1000
        if i >= a.warmup:
            rtts.append(dt)
    return {"mode": "echo", "size": a.size, "rtt_ms": summarize(rtts), "raw_rtt_ms": rtts}


def load_device(a):
    from hybrid_ecc_auth.protocol.device import Device
    from hybrid_ecc_auth.storage.keystore import KeyStore

    return Device(KeyStore(a.credential).load())


def auth(a):
    import hashlib

    h, p = addr(a.addr)
    rss_before = rss_kb()
    device = load_device(a)
    rows = []
    failures = 0
    for i in range(a.warmup + a.n):
        t0 = time.perf_counter()
        m1 = device.build_auth_request(a.server_id)
        t1 = time.perf_counter()
        with socket.create_connection((h, p), timeout=5) as s:
            _transport.send_frame(s, m1)
            resp = _transport.recv_frame(s)
        t2 = time.perf_counter()
        env = _transport.parse_envelope(resp)
        if not env["ok"]:
            failures += 1
            print("REJECTED", env, file=sys.stderr)
            continue
        m2 = env["payload"].encode("ascii")
        key = device.complete_auth(m2)
        t3 = time.perf_counter()
        if i >= a.warmup:
            rows.append(
                {
                    "build_ms": (t1 - t0) * 1000,
                    "rtt_ms": (t2 - t1) * 1000,
                    "complete_ms": (t3 - t2) * 1000,
                    "total_ms": (t3 - t0) * 1000,
                    "m1_bytes": len(m1),
                    "m2_bytes": len(m2),
                    "fp": hashlib.sha256(key).hexdigest()[:16],
                }
            )
    wall = sum(r["total_ms"] for r in rows) / 1000
    return {
        "mode": "auth",
        "n": len(rows),
        "failures": failures,
        "unique_session_keys": len({r["fp"] for r in rows}),
        "throughput_hs_per_s": len(rows) / wall if wall else 0.0,
        "m1_bytes": summarize([r["m1_bytes"] for r in rows]),
        "m2_bytes": summarize([r["m2_bytes"] for r in rows]),
        "build_ms": summarize([r["build_ms"] for r in rows]),
        "rtt_ms": summarize([r["rtt_ms"] for r in rows]),
        "complete_ms": summarize([r["complete_ms"] for r in rows]),
        "total_ms": summarize([r["total_ms"] for r in rows]),
        "device_crypto_ms": summarize([r["build_ms"] + r["complete_ms"] for r in rows]),
        "rss_kb_before_device_load": rss_before,
        "peak_rss_kb": rss_kb(),
        "raw": rows,
    }


def tamper(a):
    h, p = addr(a.addr)
    device = load_device(a)
    out = []
    for _ in range(a.n):
        m1 = json.loads(device.build_auth_request(a.server_id))
        ct = bytearray(base64.b64decode(m1["ct"]))
        ct[0] ^= 0x01
        m1["ct"] = base64.b64encode(bytes(ct)).decode()
        with socket.create_connection((h, p), timeout=5) as s:
            _transport.send_frame(s, json.dumps(m1, separators=(",", ":")).encode())
            env = _transport.parse_envelope(_transport.recv_frame(s))
        out.append(env)
        print(json.dumps(env))
    return {"mode": "tamper", "responses": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["echo-server", "echo", "auth", "tamper"])
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--addr")
    ap.add_argument("--credential")
    ap.add_argument("--server-id", default="server-A")
    ap.add_argument("-n", type=int, default=1000)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--size", type=int, default=200)
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.mode == "echo-server":
        return echo_server(a)
    res = {"echo": echo, "auth": auth, "tamper": tamper}[a.mode](a)
    s = json.dumps(res, indent=1)
    if a.out:
        open(a.out, "w").write(s)
    brief = {k: v for k, v in res.items() if not k.startswith("raw")}
    print(json.dumps(brief, indent=1)[:4000])


if __name__ == "__main__":
    main()
