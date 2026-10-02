#!/usr/bin/env python3
"""Server-side cost of resolving an unlinkable pseudonym vs number of enrolled devices.
The paper's Table V gives the server a CONSTANT cost (2*T_H + 2*T_SE/D). With PID = H2(lambda||t)
the server cannot index by PID, so it must probe (device x epoch-window) candidates."""
import os, sys, time, statistics as st
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hybrid_ecc_auth.protocol.ta import TrustedAuthority
from hybrid_ecc_auth.protocol.device import Device
from hybrid_ecc_auth.protocol.server import Server
from hybrid_ecc_auth.crypto.hashes import h2_pseudonym

print("N_devices, window(epochs), mean_resolve_ms(worst-case: device enrolled last), sha256_probes, ms_per_probe")
for n in (10, 100, 500, 1000, 5000):
    ta = TrustedAuthority(master_secret=os.urandom(32))
    manifest = [{"identity": f"dev-{i:05d}", "role": "device"} for i in range(n)] + [{"identity": "srv", "role": "server"}]
    creds = ta.enroll_batch(manifest)
    # server only needs the lambda of its devices (not the full mesh), so build that minimal table directly
    srv_cred = creds["srv"]
    srv_cred.peer_secrets = {f"dev-{i:05d}": creds[f"dev-{i:05d}"].lam for i in range(n)}
    server = Server(srv_cred)
    last = f"dev-{n-1:05d}"                       # dict order => scanned last: worst case
    dev = Device(creds[last]); dev.credential.peer_secrets["srv"] = srv_cred.lam
    times = []
    for _ in range(5):
        m1 = dev.build_auth_request("srv")
        from hybrid_ecc_auth.protocol.messages import Message1
        pid = Message1.from_bytes(m1).pid
        t0 = time.perf_counter(); server.resolve_pseudonym(pid); times.append((time.perf_counter() - t0) * 1000)
        server.handle_auth_request(m1)             # accept so the window advances like in real use
    w = len(server.session_log.epoch_search_window(last))
    probes = n * w
    print(f"{n:9d}, {w:12d}, {st.mean(times):10.2f}, {probes:9d}, {st.mean(times)/probes*1000:.2f} us")
