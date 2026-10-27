#!/usr/bin/env python3
"""Show the session keys are not forward secret: an attacker who later obtains the pairwise root k*
(e.g. one extracted device) recovers every PAST session key from recorded M1/M2 alone."""
import hashlib, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hybrid_ecc_auth.protocol.ta import TrustedAuthority
from hybrid_ecc_auth.protocol.device import Device
from hybrid_ecc_auth.protocol.server import Server
from hybrid_ecc_auth.protocol.messages import Message1, Message2
from hybrid_ecc_auth.protocol.entity import derive_session_key
from hybrid_ecc_auth.crypto import aead

ta = TrustedAuthority(master_secret=os.urandom(32))
creds = ta.enroll_batch([{"identity": "dev", "role": "device"}, {"identity": "srv", "role": "server"}])
ta.share_mutual_peer_keys(list(creds.values()))
dev, srv = Device(creds["dev"]), Server(creds["srv"])

recorded, real_keys = [], []                       # what a passive eavesdropper sees / ground truth
for _ in range(5):
    m1 = dev.build_auth_request("srv")
    res = srv.handle_auth_request(m1)
    key = dev.complete_auth(res.response_bytes)
    assert key == res.session_key
    recorded.append((m1, res.response_bytes)); real_keys.append(key)

k_star = dev.get_pairwise_root("srv")              # attacker obtains k* AFTER the sessions ended
ok = 0
for (m1b, m2b), real in zip(recorded, real_keys):
    m1, m2 = Message1.from_bytes(m1b), Message2.from_bytes(m2b)
    pt1 = aead.decrypt(k_star, m1.gcm_nonce, m1.ciphertext, m1.tag)
    pid, n_i, epoch = pt1[:32], pt1[32:-8], int.from_bytes(pt1[-8:], "big")
    pt2 = aead.decrypt(k_star, m2.gcm_nonce, m2.ciphertext, m2.tag, aad=pid + n_i)
    n_j = pt2[:-8]
    ok += derive_session_key(k_star, n_i, n_j, epoch) == real
print(f"recovered {ok}/{len(recorded)} past session keys from recorded traffic + k* alone")
print("Eq. 16 K = KDF(k* || N_i || N_j || t): all inputs besides k* travel (encrypted only under k*), so no forward secrecy.")
