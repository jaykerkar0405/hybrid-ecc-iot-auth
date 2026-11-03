#!/usr/bin/env python3
"""Measure the server-side cost of every pseudonym-resolution strategy and
check it against its closed form.

For each strategy and each number n of devices enrolled at one server, the
script builds the server state in steady state (every device has
authenticated before), resolves pseudonyms of devices drawn uniformly at
random, and counts probes (H2 evaluations, or the equivalent keyed hash in
the RFID-derived schemes). It also resolves forged pseudonyms and records the
resolution state the server keeps.

Outputs (next to this file):
  measured.csv     one row per (strategy, n) actually measured
  cost_model.csv   one row per (strategy, n) for n = 0 .. N_MAX, the input of
                   the OMNeT++ model (closed form where one exists, otherwise
                   log-log interpolation of the measured values)
  summary.txt      the closed-form checks

Run from the repository root:
    python -I evaluation/resolution/resolution_costs.py [--quick]
"""
from __future__ import annotations

import csv
import math
import os
import random
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "implementation/python"))
sys.path.insert(0, str(HERE))

from hybrid_ecc_auth.crypto.hashes import h2_pseudonym  # noqa: E402
from hybrid_ecc_auth.protocol.errors import UnknownPeerError  # noqa: E402
from hybrid_ecc_auth.protocol.resolution import (  # noqa: E402
    COUNTER_BYTES,
    NONCE_CACHE_ENTRY_BYTES,
    TABLE_ENTRY_BYTES,
    ClockScan,
    ClockTable,
    CounterTable,
    LinearScan,
    TimeMemoryTable,
)
from hybrid_ecc_auth.storage.session_log import SessionLog  # noqa: E402
from rfid_schemes import KeyTree, RandomizedHashLock  # noqa: E402

QUICK = "--quick" in sys.argv
GRID = [1, 2, 5, 10, 20, 50, 100, 200, 300, 500, 700, 1000, 2000, 5000, 10000]
if QUICK:
    GRID = [1, 10, 100, 500]
N_MAX = 10000
SAMPLES = 60 if QUICK else 200
FORGED = 5
LOOKBACK, FORWARD = 16, 8            # SessionLog defaults (the original implementation)
DRIFT, EPOCH_S = 1, 60.0             # clock options: accept cur-1 .. cur+1
LIFETIME = 128                       # time-memory trade-off: epochs per device lifetime
DELTA = 32                           # key-tree branching factor
STEADY = 100                         # last accepted epoch of every device in steady state
rng = random.Random(2026)


def peers(n):
    return {f"dev-{i:05d}": int.from_bytes(os.urandom(32), "big") for i in range(n)}


def steady_log(names, last=STEADY):
    log = SessionLog(forward_tolerance=FORWARD, replay_lookback=LOOKBACK)
    for p in names:
        log._last_accepted_epoch[p] = last
    return log


class FixedClock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


def measure_wire(resolver, sec, epoch_of, samples, n):
    """Honest and forged probes for a wire-compatible resolver."""
    names = list(sec)
    honest, misses = [], 0
    for _ in range(samples):
        p = rng.choice(names)
        e = epoch_of(p)
        resolver.reset_counters()
        try:
            got = resolver.resolve(h2_pseudonym(sec[p], e))
            assert got == (p, e), (got, p, e)
            resolver.accept(p, e, os.urandom(16))
        except UnknownPeerError:
            misses += 1
        honest.append(resolver.probes + resolver.precompute_probes)
    forged = []
    for _ in range(FORGED):
        resolver.reset_counters()
        try:
            resolver.resolve(os.urandom(32))
            raise AssertionError("forged pseudonym resolved")
        except UnknownPeerError:
            pass
        forged.append(resolver.probes)
    return honest, forged, misses


def se(xs):
    return st.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0


def run(n):
    rows = []
    sec = peers(n)
    names = list(sec)

    # O1: the original linear scan
    log = steady_log(names)
    r = LinearScan(); r.attach(sec, log)
    h, f, m = measure_wire(r, sec, lambda p: log._last_accepted_epoch[p] + 1, SAMPLES if n <= 2000 else SAMPLES // 4, n)
    rows.append(dict(strategy="O1", n=n, honest_se=se(h), honest_mean=st.mean(h), honest_max=max(h), forged=st.mean(f), misses=m,
                     precompute=0, epoch_probes=0, state_bytes=r.storage_bytes(), extra_m1_bits=0))

    # O2: counter epochs, precomputed table
    log = steady_log(names)
    r = CounterTable(); r.attach(sec, log)
    pre = r.precompute_probes
    h, f, m = measure_wire(r, sec, lambda p: log._last_accepted_epoch[p] + 1, SAMPLES, n)
    rows.append(dict(strategy="O2", n=n, honest_mean=st.mean(h), honest_max=max(h), forged=st.mean(f), misses=m,
                     precompute=pre, epoch_probes=0, state_bytes=r.storage_bytes(), extra_m1_bits=0))

    # O3: clock epochs, scan. State: the nonce cache, one entry per accepted session in the
    # drift window; we charge one per device (each device authenticates once per window).
    clock = FixedClock(EPOCH_S * STEADY + 1)
    r = ClockScan(clock, epoch_seconds=EPOCH_S, drift=DRIFT); r.attach(sec, steady_log(names))
    h, f, m = measure_wire(r, sec, lambda p: STEADY, SAMPLES if n <= 2000 else SAMPLES // 4, n)
    assert r.nonce_cache_entries() == len(h)
    rows.append(dict(strategy="O3", n=n, honest_se=se(h), honest_mean=st.mean(h), honest_max=max(h), forged=st.mean(f), misses=m,
                     precompute=0, epoch_probes=0, state_bytes=NONCE_CACHE_ENTRY_BYTES * n, extra_m1_bits=0))

    # O4: clock epochs, table extended once per epoch
    r = ClockTable(clock, epoch_seconds=EPOCH_S, drift=DRIFT); r.attach(sec, steady_log(names))
    pre = r.precompute_probes
    h, f, m = measure_wire(r, sec, lambda p: STEADY, SAMPLES, n)
    clock.t += EPOCH_S
    r.reset_counters(); r.resolve(h2_pseudonym(sec[names[0]], STEADY + 1))
    per_epoch = r.precompute_probes
    clock.t -= EPOCH_S
    rows.append(dict(strategy="O4", n=n, honest_mean=st.mean(h), honest_max=max(h), forged=st.mean(f), misses=m,
                     precompute=pre, epoch_probes=per_epoch,
                     state_bytes=TABLE_ENTRY_BYTES * n * (2 * DRIFT + 1) + NONCE_CACHE_ENTRY_BYTES * n, extra_m1_bits=0))

    # Rainbow time-memory trade-off over n x LIFETIME points
    log = steady_log(names, last=-1)
    r = TimeMemoryTable(lifetime=LIFETIME); r.attach(sec, log)
    pre = r.precompute_probes
    nxt = {p: rng.randrange(LIFETIME // 2) for p in names}

    def tm_epoch(p):
        nxt[p] += 1
        return nxt[p]
    h, f, m = measure_wire(r, sec, tm_epoch, SAMPLES if n <= 2000 else SAMPLES // 4, n)
    rows.append(dict(strategy="TM", n=n, honest_mean=st.mean(h), honest_max=max(h), forged=st.mean(f), misses=m,
                     precompute=pre, epoch_probes=0, state_bytes=r.storage_bytes(), extra_m1_bits=0))

    # Randomized hash lock (challenge-response)
    keys = {p: v.to_bytes(32, "big") for p, v in sec.items()}
    cr = RandomizedHashLock(keys)
    h = []
    for _ in range(SAMPLES if n <= 2000 else SAMPLES // 4):
        p = rng.choice(names)
        cr.probes = 0
        assert cr.resolve(*cr.device_message(keys[p])) == p
        h.append(cr.probes)
    cr.probes = 0
    assert cr.resolve(os.urandom(16), os.urandom(32)) is None
    rows.append(dict(strategy="CR", n=n, honest_se=se(h), honest_mean=st.mean(h), honest_max=max(h), forged=cr.probes, misses=0,
                     precompute=0, epoch_probes=0, state_bytes=0, extra_m1_bits=8 * cr.extra_m1_bytes(n)))

    # Key tree
    tree = KeyTree(names, delta=DELTA)
    h = []
    for _ in range(SAMPLES):
        i = rng.randrange(n)
        tree.probes = 0
        assert tree.resolve(*tree.device_message(i)) == names[i]
        h.append(tree.probes)
    tree.probes = 0
    assert tree.resolve(os.urandom(16), [os.urandom(32)] * tree.depth) is None
    rows.append(dict(strategy="MW", n=n, honest_mean=st.mean(h), honest_max=max(h), forged=tree.probes, misses=0,
                     precompute=0, epoch_probes=0, state_bytes=tree.storage_bytes(),
                     extra_m1_bits=8 * tree.extra_m1_bytes(), depth=tree.depth))
    return rows


# ---- closed forms (steady state, target drawn uniformly) --------------------------------------------------------
W1 = LOOKBACK + FORWARD + 1
WT = 2 * DRIFT + 1


def tree_depth(n):
    return max(1, math.ceil(math.log(max(n, 2), DELTA) - 1e-12))


def closed(strategy, n):
    """Expected honest probes, forged probes, per-epoch probes, resolution state (bytes), extra M1 bits."""
    if n == 0:
        return 0, 0, 0, 0, 0
    if strategy == "O1":
        return (n - 1) * W1 / 2 + (LOOKBACK + 2), n * W1, 0, COUNTER_BYTES * n, 0
    if strategy == "O2":
        return 1, 0, 0, (TABLE_ENTRY_BYTES * FORWARD + COUNTER_BYTES) * n, 0
    if strategy == "O3":
        return (n - 1) * WT / 2 + 1, n * WT, 0, NONCE_CACHE_ENTRY_BYTES * n, 0
    if strategy == "O4":
        return 0, 0, n, (TABLE_ENTRY_BYTES * WT + NONCE_CACHE_ENTRY_BYTES) * n, 0
    if strategy == "CR":
        return (n + 1) / 2, n, 0, 0, 8 * 16
    raise KeyError(strategy)


EXACT = {"O1", "O2", "O3", "O4", "CR"}


def main():
    measured = []
    for n in GRID:
        rows = run(n)
        measured += rows
        print(f"n={n:6d}  " + "  ".join(f"{r['strategy']}={r['honest_mean']:.1f}" for r in rows), flush=True)

    fields = ["strategy", "n", "honest_mean", "honest_se", "honest_max", "forged", "misses", "precompute", "epoch_probes",
              "state_bytes", "extra_m1_bits", "depth"]
    with open(HERE / "measured.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in measured:
            w.writerow({k: r.get(k, "") for k in fields})

    lines = ["Closed-form checks (steady state; honest = mean over uniformly drawn devices)."]
    worst = 0.0
    for r in measured:
        s, n = r["strategy"], r["n"]
        if s not in EXACT:
            continue
        h, f, e, b, x = closed(s, n)
        # O1, O3, CR: the target position is random, so the sample mean has sampling error;
        # allow 4 observed standard errors. O2 and O4 are deterministic and must match exactly.
        tol = 4 * r["honest_se"] + 1e-9 if s in ("O1", "O3", "CR") else 1e-9
        assert abs(r["honest_mean"] - h) <= tol, (s, n, r["honest_mean"], h)
        assert r["forged"] == f, (s, n, r["forged"], f)
        if s == "O4":
            assert r["epoch_probes"] == e, (s, n, r["epoch_probes"], e)
        if s in ("O1", "O2", "O4"):
            assert abs(r["state_bytes"] - b) < 1e-6, (s, n, r["state_bytes"], b)
        if s in ("O1", "O3", "CR"):
            assert r["honest_max"] <= (n - 1) * (W1 if s == "O1" else WT if s == "O3" else 1) + (LOOKBACK + 2 if s == "O1" else 1)
        worst = max(worst, abs(r["honest_mean"] - h) / max(h, 1))
    lines.append(f"O1, O2, O3, O4, CR: forged, per-epoch and state exact at every n; O2 and O4 honest exact; "
                 f"O1, O3, CR honest means within 4 observed SE (largest relative deviation {100 * worst:.2f}%).")
    for r in measured:
        if r["strategy"] == "MW":
            d = r["depth"]
            assert r["honest_max"] <= DELTA * d and r["forged"] <= DELTA
    lines.append(f"MW (delta={DELTA}): honest <= delta*depth and forged <= delta at every n.")
    tm = [r for r in measured if r["strategy"] == "TM" and r["n"] >= 10]
    ks = [r["honest_mean"] / (r["n"] * LIFETIME) ** (2 / 3) for r in tm]
    km = [r["state_bytes"] / (r["n"] * LIFETIME) ** (2 / 3) for r in tm]
    lines.append(f"TM (lifetime={LIFETIME}): honest / S^(2/3) = {min(ks):.2f} .. {max(ks):.2f}; "
                 f"state bytes / S^(2/3) = {min(km):.1f} .. {max(km):.1f}; "
                 f"misses {sum(r['misses'] for r in tm)} of {sum(SAMPLES if r['n'] <= 2000 else SAMPLES // 4 for r in tm)}.")
    (HERE / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

    # ---- cost model for OMNeT++: n = 0 .. N_MAX -----------------------------------------------------------------
    def interp(strategy, key, n):
        pts = sorted((r["n"], r[key]) for r in measured if r["strategy"] == strategy)
        if n <= pts[0][0]:
            return pts[0][1] * (n / pts[0][0] if key != "extra_m1_bits" and n < pts[0][0] else 1)
        for (a, va), (b, vb) in zip(pts, pts[1:]):
            if a <= n <= b:
                if va <= 0 or vb <= 0:
                    return va + (vb - va) * (n - a) / (b - a)
                t = (math.log(n) - math.log(a)) / (math.log(b) - math.log(a))
                return math.exp(math.log(va) + t * (math.log(vb) - math.log(va)))
        (a, va), (b, vb) = pts[-2], pts[-1]
        slope = (math.log(vb) - math.log(va)) / (math.log(b) - math.log(a))
        return vb * (n / b) ** slope

    with open(HERE / "cost_model.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["strategy", "n", "honest_probes", "forged_probes", "epoch_probes", "state_bytes", "extra_m1_bits"])
        for s in ["O1", "O2", "O3", "O4", "TM", "CR", "MW"]:
            for n in range(0, N_MAX + 1):
                if s in EXACT:
                    h, f, e, b, x = closed(s, n)
                elif n == 0:
                    h = f = e = b = x = 0
                elif s == "MW":
                    d = tree_depth(n)
                    h, f, e = interp(s, "honest_mean", n), interp(s, "forged", n), 0
                    b = 32 * sum(math.ceil(n / DELTA ** (d - level)) for level in range(1, d))
                    x = 8 * (16 + 32 * (d - 1))
                else:  # TM
                    h, f, e = interp(s, "honest_mean", n), interp(s, "forged", n), 0
                    b, x = interp(s, "state_bytes", n), 0
                w.writerow([s, n, f"{h:.4f}", f"{f:.4f}", f"{e:.4f}", f"{b:.1f}", int(x)])
    print(f"wrote {HERE / 'measured.csv'} and {HERE / 'cost_model.csv'}")


if __name__ == "__main__":
    main()
