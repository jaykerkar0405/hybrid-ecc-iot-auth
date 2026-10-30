#!/usr/bin/env python3
"""Count the primitive operations and wire bits of ONE handshake of OUR implementation (hybrid_ecc_auth), per role,
and compare with BASE Table V (device 2T_H+2T_SE/D, server 2T_H+2T_SE/D) and Table IV (4 msgs/1024 bits; text 2 msgs/264 bits).
Run: .venv/bin/python -I research/omnet_emulation/impl_profile/profile_ops.py   (repo root)"""
import collections, json, sys
sys.path.insert(0, "."); sys.path.insert(0, "research/paper_audit")
from hybrid_ecc_auth.crypto import hashes, aead
from hybrid_ecc_auth.protocol import entity, device as dev_mod, server as srv_mod
from hybrid_ecc_auth.protocol.device import Device
from hybrid_ecc_auth.protocol.server import Server
from hybrid_ecc_auth.protocol.ta import TrustedAuthority
from hybrid_ecc_auth.protocol.messages import Message1, Message2

C = collections.Counter()
def wrap(mod, name, label):
    f = getattr(mod, name)
    def g(*a, **k): C[label] += 1; return f(*a, **k)
    setattr(mod, name, g)
wrap(hashes, "_sha256", "SHA256")
wrap(aead, "encrypt", "AEAD_enc"); wrap(aead, "decrypt", "AEAD_dec")
_kdf = entity.kdf
def kdf_by_purpose(ikm, *, info=b"", salt=None, length=32):
    # Eq. 9 (pairwise root, cached after first contact) and Eq. 16 (session key) are separate KDF calls.
    C["KDF_root" if info == entity._INFO_PAIRWISE_ROOT else "KDF_session"] += 1
    return _kdf(ikm, info=info, salt=salt, length=length)
entity.kdf = kdf_by_purpose

def handshake(D, S):
    prof = {}
    C.clear(); m1 = D.build_auth_request("srv-A"); prof["device_build_M1"] = dict(C)
    C.clear(); res = S.handle_auth_request(m1); prof["server_handle_M1"] = dict(C)
    C.clear(); D.complete_auth(res.response_bytes); prof["device_complete"] = dict(C)
    dev = collections.Counter(prof["device_build_M1"]) + collections.Counter(prof["device_complete"])
    return m1, res, dict(dev), prof["server_handle_M1"]

def run(n_peers):
    ta = TrustedAuthority(master_secret=b"profile-secret")
    d = ta.enroll("dev-0", "device"); s = ta.enroll("srv-A", "server")
    others = [ta.enroll(f"dev-{i}", "device") for i in range(1, n_peers)]
    ta.share_mutual_peer_keys([s] + others + [d])  # target device enrolled last: worst-case lookup position
    D, S = Device(d), Server(s)
    m1, res, dev_ops, srv_ops = handshake(D, S)  # first contact: pairwise roots are derived and cached
    _, _, dev_warm, srv_warm = handshake(D, S)    # later handshakes reuse the cached roots
    M1, M2 = Message1.from_bytes(m1), Message2.from_bytes(res.response_bytes)
    raw = lambda m: sum(len(getattr(m, f)) for f in ("pid", "gcm_nonce", "ciphertext", "tag", "server_id") if hasattr(m, f) and isinstance(getattr(m, f), (bytes, str)) and (isinstance(getattr(m, f), bytes) or True) for _ in [0]) if False else None
    fields = lambda m: {f: len(getattr(m, f).encode() if isinstance(getattr(m, f), str) else getattr(m, f)) for f in ("pid", "server_id", "gcm_nonce", "ciphertext", "tag") if hasattr(m, f)}
    return {"peers_on_server": n_peers, "device_ops": dev_ops, "server_ops": srv_ops,
            "device_ops_warm": dev_warm, "server_ops_warm": srv_warm,
            "m1_raw_bytes": sum(fields(M1).values()), "m2_raw_bytes": sum(fields(M2).values()),
            "m1_wire_bytes": len(m1), "m2_wire_bytes": len(res.response_bytes)}

out = {n: run(n) for n in (1, 20, 100)}
json.dump(out, open("research/omnet_emulation/impl_profile/ops_profile.json", "w"), indent=1)
for n, r in out.items():
    print(f"\nserver knows {n} device(s):\n  device ops {r['device_ops']}\n  server ops {r['server_ops']}")
    print(f"  warm (roots cached): device {r['device_ops_warm']}  server {r['server_ops_warm']}")
    print(f"  raw bits M1+M2 = {(r['m1_raw_bytes']+r['m2_raw_bytes'])*8}   wire bits (JSON/base64) = {(r['m1_wire_bytes']+r['m2_wire_bytes'])*8}")
