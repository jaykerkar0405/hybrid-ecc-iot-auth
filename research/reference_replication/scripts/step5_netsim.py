#!/usr/bin/env python3
"""Step 5: discrete-event network-level simulation (SimPy) with the parameters of BASE Table II.
THIS IS NOT OMNeT++ and its numbers are not bit-comparable to BASE Figs 1-3.

Modelled: 1500 x 1500 m area, N = 100..1000 static devices, servers = 5% of N (uniform random, seeded), 10 Mbps link per server
(shared airtime, one session at a time per server), range 500 m (800 m as sensitivity), 15 us time quantum, random adversaries.
Per-operation times come from our measured constants (paper_audit CSVs); competitor schemes use BASE-style operation counts times those times.
Assumptions that BASE does not fix (and that we chose, all parameters of run()):
  * each device runs one authentication at a uniformly random time in [0, window_s]; default window_s = 10 s
  * a device authenticates to the nearest in-range server; devices with no server in range are counted as unreachable
  * server resolution set: 'reachable' = every device that can reach the server (default), 'nearest' = only devices attached to it
  * pseudonym lookup (proposed scheme only): probes = N_s x W with W = 13 epochs (measured window), t_probe = measured SHA-256 40 B
  * adversaries: 5% of N, each sends forged requests as a Poisson stream (1/s) to its nearest in-range server; a forged request costs the
    server 1 T_H for every scheme, except the proposed scheme where an unknown PID forces a full N_s x W miss scan
  * the 15 us sampling interval is used as the event-time quantum
"""
import sys
import numpy as np
import simpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import refmodel as M
import reeval
from common import write_csv, RESULTS, AUDIT, T4, T3

AREA, RATE_BPS, QUANT, W_EPOCHS = 1500.0, 10e6, 15e-6, 13
NS = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
SEEDS = [1, 2, 3, 4, 5]


def platform(csv, aes="aes_big", T_C=0.32):
    rows = reeval.load(AUDIT / "results" / csv)
    k = reeval.constants(rows, aes, "P-256 ec_p256_m15")
    t = {"H": k["H"], "SE": k["SE/D"], "ECM": k["ECM"], "fe": T3["fe"], "C": T_C, "KDF": reeval.pick(rows, "HKDF-SHA256", "bearssl")}
    return t, reeval.pick(rows, "SHA-256 (PID", " 40 B")   # ms


SCHEMES = {  # name: (ops, bits on air for one session)
    "Proposed V1 (Table V)": (M.PROPOSED["V1 Table V as printed"], 1024),
    "Proposed V2 (+KDF)": (M.PROPOSED["V2 Table V + session KDF"], 1024),
    "Turkanovic (7/5/7)": (M.turkanovic_corrected(), T4["Turkanovic [12]"][4]),
    "Dhillon-Karla": (M.base_printed()["Dhillon-Karla [13]"], T4["Dhillon-Karla [13]"][4]),
    "JIANG published": (M.jiang_published(), 1312),
    "Cheng-Le as P2 (ECC)": (M.changle_schemes()["Chang-Le P2"], T4["Cheng and Le [14]"][4] if "Cheng and Le [14]" in T4 else T4["Cheng-Le [14]"][4]),
    "Sadhukhan (ECC)": (M.base_printed()["Sadhukhan [18]"], T4["Sadhukhan [18]"][4]),
}


def server_device_costs(ops, td, ts):
    """(device_ms, server_ms). For a combined-only scheme (JIANG) the total is split evenly (role split UNVERIFIED)."""
    if "total" in ops:
        c = M.cost(ops["total"], td)
        cs = M.cost(ops["total"], ts)
        return c / 2, cs / 2
    return M.cost(ops.get("device"), td), M.cost(ops.get("server"), ts)


def run(N, name, seed, dev_const, srv_const, t_probe_ms, range_m=500.0, policy="reachable", window_s=10.0, adversaries=True, bits_override=None):
    rng = np.random.default_rng(seed)
    n_srv = max(1, round(0.05 * N))
    dpos = rng.uniform(0, AREA, (N, 2)); spos = rng.uniform(0, AREA, (n_srv, 2))
    dist = np.linalg.norm(dpos[:, None, :] - spos[None, :, :], axis=2)
    reach = dist <= range_m
    nearest = np.where(reach.any(axis=1), np.argmin(np.where(reach, dist, np.inf), axis=1), -1)
    n_enrolled = reach.sum(axis=0) if policy == "reachable" else np.bincount(nearest[nearest >= 0], minlength=n_srv)
    ops, bits = SCHEMES[name]
    if bits_override:
        bits = bits_override
    dev_ms, srv_ms = server_device_costs(ops, dev_const, srv_const)
    is_prop = name.startswith("Proposed")
    env = simpy.Environment()
    cpu = [simpy.Resource(env, 1) for _ in range(n_srv)]
    air = [simpy.Resource(env, 1) for _ in range(n_srv)]
    lat, busy, bits_on_air = [], np.zeros(n_srv), [0.0]
    q = lambda x: np.ceil(x / QUANT) * QUANT

    def serve(s, work_s):
        with cpu[s].request() as r:
            yield r
            yield env.timeout(q(work_s)); busy[s] += work_s

    def session(i, start):
        s = nearest[i]
        yield env.timeout(q(start))
        t0 = env.now
        yield env.timeout(q(dev_ms / 2e3))
        with air[s].request() as r:
            yield r
            yield env.timeout(q(bits / RATE_BPS)); bits_on_air[0] += bits
        probes = n_enrolled[s] * W_EPOCHS / 2 if is_prop else 0   # expected scan position: half the table on average
        yield env.process(serve(s, srv_ms / 1e3 + probes * t_probe_ms / 1e3))
        yield env.timeout(q(dev_ms / 2e3))
        lat.append(env.now - t0)

    def forged(a_start, s):
        t = a_start
        while t < window_s:
            t += rng.exponential(1.0)
            if t >= window_s:
                break
            yield env.timeout(max(0.0, q(t) - env.now))
            work = (n_enrolled[s] * W_EPOCHS * t_probe_ms / 1e3) if is_prop else srv_const["H"] / 1e3
            with air[s].request() as r:
                yield r
                yield env.timeout(q(128 / RATE_BPS)); bits_on_air[0] += 128
            env.process(serve(s, work))

    starts = rng.uniform(0, window_s, N)
    for i in range(N):
        if nearest[i] >= 0:
            env.process(session(i, starts[i]))
    n_adv = round(0.05 * N) if adversaries else 0
    for a in range(n_adv):
        apos = rng.uniform(0, AREA, 2); d = np.linalg.norm(spos - apos, axis=1)
        if (d <= range_m).any():
            env.process(forged(0.0, int(np.argmin(np.where(d <= range_m, d, np.inf)))))
    env.run()
    unreachable = int((nearest < 0).sum())
    lat = np.array(lat) if lat else np.array([np.nan])
    return {"lat_mean_ms": 1e3 * lat.mean(), "lat_p95_ms": 1e3 * np.percentile(lat, 95), "kbit_on_air": bits_on_air[0] / 1e3,
            "server_busy_ms_total": 1e3 * busy.sum(), "server_busy_ms_max": 1e3 * busy.max(), "unreachable": unreachable,
            "mean_enrolled_per_server": float(n_enrolled.mean()), "makespan_s": env.now}


def sweep(dev_const, srv_const, t_probe, label, **kw):
    rows = []
    for name in SCHEMES:
        for N in NS:
            rs = [run(N, name, sd, dev_const, srv_const, t_probe, **kw) for sd in SEEDS]
            agg = {k: float(np.mean([r[k] for r in rs])) for k in rs[0]}
            rows.append((label, name, N, *(round(agg[k], 4) for k in ("lat_mean_ms", "lat_p95_ms", "kbit_on_air", "server_busy_ms_total", "server_busy_ms_max", "unreachable", "mean_enrolled_per_server", "makespan_s"))))
    return rows


HDR = ["config", "scheme", "N_devices", "lat_mean_ms", "lat_p95_ms", "kbit_on_air", "server_busy_ms_total", "server_busy_ms_max", "unreachable_devices", "mean_enrolled_per_server", "makespan_s"]


def main():
    dev80, _ = platform("esp8266_80mhz.csv")
    srv_esp, tp_esp = platform("esp8266_80mhz.csv")
    srv_mac, tp_mac = platform("mac.csv")
    all_rows = []
    cfgs = [
        ("devices ESP8266, server ESP8266, T_C=0.32, range 500, reachable", dev80, srv_esp, tp_esp, {}),
        ("devices ESP8266, server laptop, T_C=0.32, range 500, reachable", dev80, srv_mac, tp_mac, {}),
        ("devices ESP8266, server ESP8266, T_C=0.32, range 500, nearest-only", dev80, srv_esp, tp_esp, {"policy": "nearest"}),
        ("devices ESP8266, server ESP8266, T_C=0.32, range 800, reachable", dev80, srv_esp, tp_esp, {"range_m": 800.0}),
    ]
    dev_c = platform("esp8266_80mhz.csv", T_C=32.40)[0]; srv_c = platform("esp8266_80mhz.csv", T_C=32.40)[0]
    cfgs.append(("devices ESP8266, server ESP8266, T_C=32.40, range 500, reachable", dev_c, srv_c, tp_esp, {}))
    for label, dc, sc, tp, kw in cfgs:
        print("running:", label, flush=True)
        all_rows += sweep(dc, sc, tp, label, **kw)
    write_csv(RESULTS / "step5_netsim.csv", HDR, all_rows)
    plots(all_rows)
    # server busy time and window sensitivity at N = 1000, proposed scheme
    rows = []
    for w in (1.0, 10.0, 60.0):
        for name in ("Proposed V1 (Table V)", "Dhillon-Karla"):
            for adv in (True, False):
                r = np.mean([run(1000, name, sd, dev80, srv_esp, tp_esp, window_s=w, adversaries=adv)["lat_mean_ms"] for sd in SEEDS])
                rows.append((w, name, "adversaries on" if adv else "adversaries off", round(float(r), 3)))
    write_csv(RESULTS / "step5_window_sensitivity.csv", ["window_s", "scheme", "adversaries", "mean_latency_ms_N1000_esp8266_server"], rows)
    print("window sensitivity:", rows)


def plots(rows):
    cfg = "devices ESP8266, server ESP8266, T_C=0.32, range 500, reachable"
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    for name in SCHEMES:
        sel = [r for r in rows if r[0] == cfg and r[1] == name]
        x = [r[2] for r in sel]
        ax[0].plot(x, [r[3] for r in sel], marker="o", ms=3, label=name)
        ax[1].plot(x, [r[5] for r in sel], marker="o", ms=3, label=name)
        ax[2].plot(x, [r[6] for r in sel], marker="o", ms=3, label=name)
    ax[0].set(xlabel="devices", ylabel="mean authentication latency (ms, log)", yscale="log", title="Latency (cf. BASE Fig. 1 'processing')")
    ax[1].set(xlabel="devices", ylabel="kbit on air, all sessions + forged", yscale="log", title="Bits on air (cf. BASE Fig. 2)")
    ax[2].set(xlabel="devices", ylabel="total server busy time (ms, log)", yscale="log", title="Server work")
    ax[0].legend(fontsize=7)
    fig.suptitle("SimPy network model with BASE Table II parameters (NOT OMNeT++); ESP8266-class devices and server, 5 seeds")
    fig.tight_layout(); fig.savefig(RESULTS / "step5_cost_vs_devices.png", dpi=150); plt.close(fig)
    # storage: BASE Table VI constant vs O(N x W) pseudonym table (32 B each)
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    x = np.array(NS)
    ax.plot(x, [320] * len(x), label="BASE Table VI server storage (320 bit)")
    ax.plot(x, x * 0.2 * W_EPOCHS * 32 * 8, label="precomputed PID table, ~0.2N enrolled x 13 epochs x 256 bit (model)")
    ax.set(xlabel="devices", ylabel="server storage (bits, log)", yscale="log", title="Storage vs devices (cf. BASE Fig. 3)")
    ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(RESULTS / "step5_storage_vs_devices.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    main()
