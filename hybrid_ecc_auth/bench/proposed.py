"""BR-1.1, BR-2.1, BR-3.1: cost model for the *proposed* scheme, driven
entirely by real crypto/protocol calls -- no assumed timing constants.

Per PRD Section 6.2, this module measures actual operation costs on the
benchmarking host (real AES-GCM, real HKDF, real SHA-256 via the
`cryptography` bindings to OpenSSL) rather than reusing the paper's
assumed Table III constants. See bench/report.py for where those paper
constants are instead plugged into the *baseline* schemes' published
formulas for an analytical side-by-side.
"""

from __future__ import annotations

import json
import statistics
import time

from ..protocol.device import Device
from ..protocol.messages import Message1, Message2
from ..protocol.server import Server
from ..protocol.ta import TrustedAuthority

BENCH_DEVICE_ID = "bench-device-000"
BENCH_SERVER_ID = "bench-server-A"


def _provision_pair(master_secret: bytes = b"bench-fixed-secret-do-not-use-in-prod"):
    ta = TrustedAuthority(master_secret=master_secret)
    device_cred = ta.enroll(BENCH_DEVICE_ID, "device")
    server_cred = ta.enroll(BENCH_SERVER_ID, "server")
    ta.share_mutual_peer_keys([device_cred, server_cred])
    return ta, device_cred, server_cred


def _json_len(obj) -> int:
    return len(json.dumps(obj, separators=(",", ":")).encode("utf-8"))


# --- BR-1: communication cost -----------------------------------------


def measure_communication_cost() -> dict:
    """BR-1.1: exact wire-message sizes for a real M1/M2 exchange, broken
    down by field. BR-1.2: the (zero) offline registration wire cost --
    FR-2.3 makes registration a purely local/offline computation."""
    _ta, device_cred, server_cred = _provision_pair()
    device = Device(device_cred)
    server = Server(server_cred)

    msg1_bytes = device.build_auth_request(BENCH_SERVER_ID)
    msg1 = Message1.from_bytes(msg1_bytes)
    result = server.handle_auth_request(msg1_bytes)
    msg2_bytes = result.response_bytes
    msg2 = Message2.from_bytes(msg2_bytes)
    device.complete_auth(msg2_bytes)

    m1_fields = {
        "pid": len(msg1.pid),
        "gcm_nonce": len(msg1.gcm_nonce),
        "ciphertext": len(msg1.ciphertext),
        "tag": len(msg1.tag),
    }
    m2_fields = {
        "server_id_utf8": len(msg2.server_id.encode("utf-8")),
        "gcm_nonce": len(msg2.gcm_nonce),
        "ciphertext": len(msg2.ciphertext),
        "tag": len(msg2.tag),
    }

    return {
        "unit": "bytes (wire-serialized: base64-in-JSON envelope, see protocol/messages.py)",
        "m1_wire_bytes": len(msg1_bytes),
        "m1_field_breakdown_raw_bytes": m1_fields,
        "m2_wire_bytes": len(msg2_bytes),
        "m2_field_breakdown_raw_bytes": m2_fields,
        "session_total_wire_bytes": len(msg1_bytes) + len(msg2_bytes),
        "session_total_raw_field_bytes": sum(m1_fields.values()) + sum(m2_fields.values()),
        "offline_registration_wire_bytes": 0,
        "offline_registration_note": (
            "FR-2.3: TA<->device/server registration performs no network I/O "
            "in this implementation -- lambda_X is derived and installed "
            "entirely locally/offline, so there is no wire message to size "
            "(unlike the paper's Section II registration Msg-I..IV, which "
            "this PoC deliberately does not implement -- see PRD 1.2 design "
            "decision)."
        ),
    }


# --- BR-2: processing cost -----------------------------------------------


def _stats(samples: list[float]) -> dict:
    sorted_samples = sorted(samples)
    p95_index = min(len(sorted_samples) - 1, round(0.95 * (len(sorted_samples) - 1)))
    return {
        "n": len(samples),
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "p95_ms": sorted_samples[p95_index],
        "stddev_ms": statistics.pstdev(samples) if len(samples) > 1 else 0.0,
    }


def measure_processing_cost(n_trials: int = 1000) -> dict:
    """BR-2.1: time real device-side and server-side operations.

    Reports two regimes:
      - "warm": FR-3.2's steady-state cache hit -- k*_ij derived once, then
        reused across sessions (this implementation's actual behavior).
      - "cold": the pairwise root is force-recomputed (1 fresh KDF call)
        before every single session, matching the paper's Eq. 22 literal
        per-session cost model (1 KDF + ... every time). Run over fewer
        trials since each one repeats the KDF derivation.
    """
    _ta, device_cred, server_cred = _provision_pair()

    device_warm = Device(device_cred)
    server_warm = Server(server_cred)
    device_warm.get_pairwise_root(BENCH_SERVER_ID)  # prime FR-3.2 cache
    server_warm.get_pairwise_root(BENCH_DEVICE_ID)

    device_build_samples: list[float] = []
    device_complete_samples: list[float] = []
    server_handle_samples: list[float] = []

    for _ in range(n_trials):
        t0 = time.perf_counter()
        msg1 = device_warm.build_auth_request(BENCH_SERVER_ID)
        t1 = time.perf_counter()
        result = server_warm.handle_auth_request(msg1)
        t2 = time.perf_counter()
        device_warm.complete_auth(result.response_bytes)
        t3 = time.perf_counter()
        device_build_samples.append((t1 - t0) * 1000.0)
        server_handle_samples.append((t2 - t1) * 1000.0)
        device_complete_samples.append((t3 - t2) * 1000.0)

    device_total_warm = [b + c for b, c in zip(device_build_samples, device_complete_samples)]

    n_cold_trials = max(50, n_trials // 10)
    device_cold = Device(device_cred)
    server_cold = Server(server_cred)
    device_cold_total_samples: list[float] = []
    server_cold_total_samples: list[float] = []

    for _ in range(n_cold_trials):
        device_cold.invalidate_pairwise_root()
        server_cold.invalidate_pairwise_root()
        t0 = time.perf_counter()
        msg1 = device_cold.build_auth_request(BENCH_SERVER_ID)
        t1 = time.perf_counter()
        result = server_cold.handle_auth_request(msg1)
        t2 = time.perf_counter()
        device_cold.complete_auth(result.response_bytes)
        t3 = time.perf_counter()
        device_cold_total_samples.append(((t1 - t0) + (t3 - t2)) * 1000.0)
        server_cold_total_samples.append((t2 - t1) * 1000.0)

    return {
        "unit": "milliseconds, wall-clock, measured on this benchmarking host",
        "n_trials": n_trials,
        "warm_steady_state_pairwise_root_cached_FR_3_2": {
            "device_build_request": _stats(device_build_samples),
            "device_complete_auth": _stats(device_complete_samples),
            "device_total": _stats(device_total_warm),
            "server_handle_request": _stats(server_handle_samples),
        },
        "cold_pairwise_root_recomputed_every_session_matches_paper_Eq22": {
            "n_trials": n_cold_trials,
            "device_total": _stats(device_cold_total_samples),
            "server_total": _stats(server_cold_total_samples),
        },
    }


# --- BR-3: storage cost --------------------------------------------------


def measure_storage_cost() -> dict:
    """BR-3.1: actual serialized byte size of per-entity persisted state
    (credential bundle, cached k*_ij, block-list, epoch counters), after
    exercising one real session so the state resembles steady-state."""
    _ta, device_cred, server_cred = _provision_pair()
    device = Device(device_cred)
    server = Server(server_cred)

    msg1 = device.build_auth_request(BENCH_SERVER_ID)
    result = server.handle_auth_request(msg1)
    device.complete_auth(result.response_bytes)

    device_state = {
        "credential": device_cred.to_dict(),
        "pairwise_root_cache": {k: v.hex() for k, v in device._pairwise_root_cache.items()},
        "epoch_counters": dict(device._epoch),
    }
    server_state = {
        "credential": server_cred.to_dict(),
        "pairwise_root_cache": {k: v.hex() for k, v in server._pairwise_root_cache.items()},
        "last_accepted_epoch": dict(server.session_log._last_accepted_epoch),
        "block_list": sorted(server.session_log._blocked),
    }

    return {
        "unit": "bytes (JSON-serialized persisted state, this implementation's actual layout)",
        "device_persisted_state_bytes": _json_len(device_state),
        "server_persisted_state_bytes": _json_len(server_state),
        "device_state_breakdown_bytes": {k: _json_len(v) for k, v in device_state.items()},
        "server_state_breakdown_bytes": {k: _json_len(v) for k, v in server_state.items()},
    }
