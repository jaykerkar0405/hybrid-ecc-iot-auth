#!/usr/bin/env python3
"""Run the project's real Python Server and drive the C device against it.

  python firmware/esp8266/tools/interop.py            # native C client (no hardware)
  python firmware/esp8266/tools/interop.py --listen   # just serve; point the ESP8266 at it

Both modes print the session-key fingerprint the Python server derived, so it
can be compared with the fingerprint the C device prints."""
import argparse, hashlib, json, os, socket, subprocess, sys, tempfile, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from hybrid_ecc_auth.demo import _transport
from hybrid_ecc_auth.protocol.errors import AuthenticationError
from hybrid_ecc_auth.protocol.messages import MessageFormatError
from hybrid_ecc_auth.protocol.server import Server
from hybrid_ecc_auth.protocol.ta import TrustedAuthority

DEVICE, SERVER = "esp8266-001", "server-A"


def enroll(master: bytes):
    ta = TrustedAuthority(master_secret=master)
    creds = ta.enroll_batch([{"identity": DEVICE, "role": "device"}, {"identity": SERVER, "role": "server"}])
    ta.share_mutual_peer_keys(list(creds.values()))
    return creds[DEVICE], creds[SERVER]


def serve(server: Server, sock: socket.socket, log: list):
    while True:
        try:
            conn, addr = sock.accept()
        except OSError:
            return
        with conn:
            try:
                req = _transport.recv_frame(conn)
                res = server.handle_auth_request(req)
                fp = hashlib.sha256(res.session_key).hexdigest()[:16]
                log.append(("accepted", fp))
                print(f"[server] accepted {res.peer_identity} from {addr[0]} fp={fp}", flush=True)
                _transport.send_frame(conn, _transport.build_ok_envelope(res.response_bytes))
            except (AuthenticationError, MessageFormatError) as exc:
                log.append(("rejected", type(exc).__name__))
                print(f"[server] rejected {type(exc).__name__}: {exc}", flush=True)
                _transport.send_frame(conn, _transport.build_error_envelope(type(exc).__name__, str(exc)))
            except ConnectionError:
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen", action="store_true")
    ap.add_argument("--port", type=int, default=8443)
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--master-hex", default=None, help="reuse a TA master secret (hex); default: random")
    a = ap.parse_args()

    saved = ROOT / "firmware/esp8266/.creds/master.hex"
    if a.master_hex:
        master = bytes.fromhex(a.master_hex)
    elif a.listen and saved.exists():
        master = bytes.fromhex(saved.read_text().strip())  # same enrollment as the flashed board
    else:
        master = os.urandom(32)
    dev, srv = enroll(master)
    lam_d = dev.lam.to_bytes(32, "big").hex()
    lam_s = dev.peer_secrets[SERVER].to_bytes(32, "big").hex()
    server = Server(srv)
    log: list = []
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0" if a.listen else "127.0.0.1", a.port))
    sock.listen(5)
    threading.Thread(target=serve, args=(server, sock, log), daemon=True).start()

    if a.listen:
        print(f"[server] listening on :{a.port}; device {DEVICE!r} lam={lam_d}\n         server lam={lam_s}", flush=True)
        threading.Event().wait()
    binary = ROOT / "firmware/esp8266/host/host_test"
    out = subprocess.run([str(binary), lam_d, lam_s, SERVER, "127.0.0.1", str(a.port), str(a.n)],
                         capture_output=True, text=True)
    print(out.stdout, end="")
    c_fps = [l.split("fp=")[1] for l in out.stdout.splitlines() if "RESULT ok" in l]
    s_fps = [v for k, v in log if k == "accepted"]
    match = c_fps == s_fps and len(c_fps) == a.n
    print(f"session keys agree for {len(c_fps)}/{a.n} handshakes: {match}")
    print(f"server rejected replay: {log[-1] if log else None}")
    sys.exit(0 if match and out.returncode == 0 else 1)


if __name__ == "__main__":
    main()
