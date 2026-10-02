#!/usr/bin/env python3
"""Consistency audit of the paper's cost claims, using only the paper's own tables."""
import statistics as st
from paper_tables import T3, T4, T5, T6

def cost(ops, t=T3):
    return 0.0 if ops is None else sum(n * t[k] for k, n in ops.items())

def role_costs(scheme, t=T3):
    r = T5[scheme]
    return cost(r["user"], t), cost(r["device"], t), cost(r["server"], t)

def reductions(vals, prop):
    others = {k: v for k, v in vals.items() if k != "Proposed scheme"}
    pct = lambda ref: 100 * (1 - prop / ref)
    return {
        "vs best": (min(others, key=others.get), pct(min(others.values()))),
        "vs mean": (None, pct(st.mean(others.values()))),
        "vs median": (None, pct(st.median(others.values()))),
        "vs worst": (max(others, key=others.get), pct(max(others.values()))),
        "per scheme": {k: pct(v) for k, v in others.items()},
    }

def show(title, vals, prop, unit):
    print(f"\n=== {title} ===")
    for k, v in sorted(vals.items(), key=lambda kv: kv[1]):
        print(f"  {k:20s} {v:10.2f} {unit}")
    r = reductions(vals, prop)
    for k in ("vs best", "vs mean", "vs median", "vs worst"):
        name, p = r[k]
        print(f"  proposed {k:10s}: {p:6.1f}% {'('+name+')' if name else ''}")

print("Table III constants (ms):", T3)

# --- Processing (Table V x Table III) ---
for label, pick in (("device + server", lambda u, d, s: d + s), ("user + device + server", lambda u, d, s: u + d + s)):
    vals = {k: pick(*role_costs(k)) for k in T5}
    show(f"Processing, Table V x Table III, {label}", vals, vals["Proposed scheme"], "ms")
    wins = [k for k, v in vals.items() if k != "Proposed scheme" and v < vals["Proposed scheme"]]
    print(f"  schemes CHEAPER than proposed under the paper's own constants: {wins}")

# --- Communication (Table IV) ---
tot = {k: v[4] for k, v in T4.items()}
show("Communication, Table IV totals", tot, tot["Proposed scheme"], "bits")
print("  Table IV says the proposed scheme uses", T4["Proposed scheme"][0], "messages; Sec. III-E / Eq. 21 / Sec. V-B say two.")
print("  Sec. V-B: '128 bits per message, therefore 264 bits total' -> 2 x 128 =", 2 * 128, "(not 264)")
print("  Table IV total 1024 vs text 264: factor", round(1024 / 264, 2))
fig = {k: v[4] for k, v in T4.items()}
tot264 = dict(fig); tot264["Proposed scheme"] = 264
r = reductions(tot264, 264)
print("  if 264 bits were used instead: vs best %.1f%%, vs mean %.1f%%" % (r["vs best"][1], r["vs mean"][1]))

# --- Storage (Table VI) ---
srv = {k: v[0] for k, v in T6.items()}; dev = {k: v[1] for k, v in T6.items()}; both = {k: v[0] + v[1] for k, v in T6.items()}
for name, vals in (("server", srv), ("device", dev), ("server+device", both)):
    show(f"Storage, Table VI, {name}", vals, vals["Proposed scheme"], "bits")
print("  Table VI caption reads 'Comparative Analysis of the Communication Cost' (sic).")

# --- What the abstract claims ---
print("\n=== Abstract claims: ~17% communication, ~21% processing, ~12% storage ===")
print("  Reproducible from Tables IV-VI? compare the 'vs best/mean/median/worst' lines above.")
print("  Note Figs. 1-3 compare against a DIFFERENT scheme set (Gope, Gupta, Hassan, Zhanfei);")
print("  their underlying values are not tabulated, so the abstract percentages cannot be recomputed from the paper.")

# --- crossover ratios: when does the proposed scheme beat the hash-only schemes? ---
print("\n=== Crossover: proposed (2H + 2SE/D per side) vs hash-only schemes, as a function of r = T_SE/D / T_H ===")
print("  (independent of absolute ms; Table III has r = %.1f)" % (T3["SE/D"] / T3["H"]))
for name in ("Turkanovic [12]", "Dhillon-Karla [13]", "Jiang [15]"):
    u, d, s = (T5[name][k] for k in ("user", "device", "server"))
    hs = lambda o: o["H"]
    dev_h, srv_h, usr_h = hs(d), hs(s), hs(u)
    # proposed device+server = 4H + 4R*H(=SE/D) ; scheme = (dev_h+srv_h) H
    r_dev_srv = ((dev_h + srv_h) - 4) / 4
    r_all = ((usr_h + dev_h + srv_h) - 4) / 4
    r_dev = (dev_h - 2) / 2
    print(f"  vs {name:20s}: proposed cheaper iff r < {r_dev:.2f} (device col only), r < {r_dev_srv:.2f} (device+server), r < {r_all:.2f} (all cols)")
