#!/usr/bin/env python3
"""Recompute the paper's Table V with MEASURED primitive costs instead of Table III.

Method: operation counts per role come from the paper's Table V (unchanged); the
per-operation times T_H, T_SE/D, T_ECM come from our benchmark of the same BearSSL
code on each platform. T_C (Chebyshev) and T_fe (fuzzy extractor) are not measured
and keep the paper's Table III values (they only matter for Challa and Wazid).
Competitor protocols are NOT re-implemented: their cost is the paper's op count
times our measured primitive time.
"""
import csv, sys, statistics as st
from pathlib import Path
from paper_tables import T3, T5

RES = Path(__file__).parent / "results"

def load(path):
    rows = {}
    for r in csv.reader(open(path)):
        if r and r[0] == "BENCH":
            # labels may contain commas: the last 8 fields are numeric, op is field 2, variant is the rest
            nums, mid = r[-8:], r[2:-8]
            rows[(mid[0], ",".join(mid[1:]))] = float(nums[3]) / 1000.0  # median us -> ms
    return rows

def pick(rows, op, variant):
    """Median ms for the row whose op starts with `op`. `variant` is 'impl' or 'impl/key':
    the row's variant must start with impl and (if given) end with '/key'."""
    impl, _, key = variant.partition("/")
    for (o, v), ms in rows.items():
        if o.startswith(op) and v.startswith(impl) and (not key or v.endswith("/" + key)):
            return ms
    raise KeyError((op, variant))

def constants(rows, aes, ec):
    return {
        "H": pick(rows, "T_H: SHA-1", "bearssl"),
        "SE/D": pick(rows, "AES-GCM encrypt+tag", f"{aes}/AES-256"),
        "ECM": pick(rows, "T_ECM", ec),
        "C": T3["C"], "fe": T3["fe"],  # modelled, not measured
    }

def cost(ops, t): return 0.0 if ops is None else sum(n * t[k] for k, n in ops.items())
def totals(t):
    out = {}
    for k, r in T5.items():
        out[k] = (cost(r["user"], t), cost(r["device"], t), cost(r["server"], t))
    return out

def report(name, rows):
    print(f"\n##### {name}")
    ec_variants = [v for (o, v) in rows if o.startswith("T_ECM")]
    best_ec = "P-256 ec_p256_m15"  # the same implementation on every platform (the MCU core ships no m31)
    for aes in ("aes_big", "aes_small", "aes_ct"):
        t = constants(rows, aes, best_ec)
        r = t["SE/D"] / t["H"]
        print(f"\n[{aes} | {best_ec}]  T_H={t['H']*1000:.1f} us  T_SE/D={t['SE/D']*1000:.1f} us  T_ECM={t['ECM']:.2f} ms  "
              f"r=T_SE/D/T_H={r:.1f} (paper: 17.5; proposed beats hash-only schemes only if r < 2.0-4.5)")
        tot = totals(t)
        prop = sum(tot["Proposed scheme"])
        print(f"  {'scheme':22s} {'device+server ms':>17s} {'all roles ms':>13s}   vs proposed (all roles)")
        for k, (u, d, s) in sorted(tot.items(), key=lambda kv: sum(kv[1])):
            print(f"  {k:22s} {d+s:17.3f} {u+d+s:13.3f}   {'(proposed)' if k=='Proposed scheme' else f'{sum((u,d,s))/prop:6.2f}x'}")
        cheaper = [k for k, v in tot.items() if k != "Proposed scheme" and sum(v) < prop]
        print(f"  schemes cheaper than proposed: {cheaper}")
    return best_ec


# ---- sensitivity of the ranking to how T_SE/D and T_H are defined --------------------------------
HASH_ONLY = ("Turkanovic [12]", "Dhillon-Karla [13]", "Jiang [15]")
S_DEFS = [  # (label, op prefix, variant template). {a} = aes implementation
    ("GCM 56 B incl. key schedule", "AES-GCM encrypt+tag (incl", "{a}/AES-256"),
    ("GCM 56 B, key schedule cached", "AES-256-GCM encrypt 56 B (key schedule cached)", "{a}"),
    ("CTR 56 B, cached key, no GHASH", "AES-256-CTR 56 B", "{a}"),
    ("1 AES block, cached key", "AES-256 single block", "{a}"),
]
H_DEFS = [("SHA-1 1 block", "T_H: SHA-1 (paper"), ("SHA-1 2 blocks", "T_H: SHA-1 (2 blocks)")]

def grid(name, rows):
    print(f"\n##### sensitivity grid: {name}   (r = T_SE/D / T_H; hash-only schemes win when r exceeds ~2.0-4.5; paper r = 17.5)")
    ec = pick(rows, "T_ECM", "P-256 ec_p256_m15")
    print(f"  {'T_SE/D definition':32s} {'AES impl':10s} {'T_H def':15s} {'r':>6s}  hash-only schemes cheaper than proposed (device+server | all roles)")
    flips = 0
    for sl, sop, svar in S_DEFS:
        for a in ("aes_big", "aes_small", "aes_ct"):
            try: ts = pick(rows, sop, svar.format(a=a))
            except KeyError: continue
            for hl, hop in H_DEFS:
                try: th = pick(rows, hop, "bearssl")
                except KeyError: continue
                t = {"H": th, "SE/D": ts, "ECM": ec, "C": T3["C"], "fe": T3["fe"]}
                tot = totals(t); prop = tot["Proposed scheme"]
                ds = [k for k in HASH_ONLY if tot[k][1] + tot[k][2] < prop[1] + prop[2]]
                al = [k for k in HASH_ONLY if sum(tot[k]) < sum(prop)]
                flips += (len(ds) < 3) or (len(al) < 3)
                print(f"  {sl:32s} {a:10s} {hl:15s} {ts/th:6.1f}  {len(ds)}/3 | {len(al)}/3")
    print(f"  cells where the proposed scheme beats at least one hash-only scheme: {flips}")

if __name__ == "__main__":
    print("Paper's Table III for reference:", T3)
    for f in sys.argv[1:]:
        report(Path(f).stem, load(f))
        grid(Path(f).stem, load(f))
