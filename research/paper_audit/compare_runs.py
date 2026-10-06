#!/usr/bin/env python3
"""Compare benchmark runs: medians per (op, variant) and output checksums.
usage: compare_runs.py   (paths are fixed below; raw ESP8266 serial captures are parsed directly)"""
import statistics as st, sys
from pathlib import Path
HERE = Path(__file__).parent; RES = HERE / "results"; NEW = RES / "rerun_2026-10-06"
SCR = Path(sys.argv[1]) if len(sys.argv) > 1 else None   # scratch dir with the raw board captures

def parse(lines):
    med, dig = {}, {}
    for l in lines:
        l = l.strip().replace("\r", "")
        if l.startswith("BENCH,"):
            f = l.split(","); nums, mid = f[-8:], f[2:-8]
            med.setdefault((mid[0], ",".join(mid[1:])), float(nums[3]))          # first occurrence wins
        elif l.startswith("BENCH_CHECK,"):
            f = l.split(","); dig.setdefault(f[2], []).append(f[-1])
    return med, dig
def csv(p): return parse(open(p, errors="replace").read().splitlines())
def raw(p): return parse(open(p, "rb").read().decode("latin1").splitlines())

def compare(name, a, b, tol=0.05, floor_us=1.0):
    (ma, da), (mb, db) = a, b
    keys = [k for k in ma if k in mb]
    dev = [(abs(mb[k] / ma[k] - 1), k) for k in keys if ma[k] > 0]
    big = sorted([d for d in dev if d[0] > tol], reverse=True)
    meaningful = [d for d in big if ma[d[1]] >= floor_us]   # ignore sub-microsecond host rows (timer-resolution noise)
    dig_bad = [k for k in da if k in db and da[k] != db[k]]
    print(f"\n== {name}: {len(keys)} rows in common; median |dev| {st.median(d[0] for d in dev)*100:.2f}%; "
          f"max {max(d[0] for d in dev)*100:.2f}%; rows off by >{tol*100:.0f}%: {len(big)} ({len(meaningful)} with a baseline >= {floor_us:g} us)")
    for d, k in meaningful[:6]: print(f"     {d*100:6.1f}%  {k[0][:60]} | {k[1][:30]}")
    print(f"   output digests compared: {sum(len(v) for k,v in da.items() if k in db)}  mismatches: {len(dig_bad)}")

old = {"mac": csv(RES / "mac.csv"), "libcrypto": csv(RES / "mac_libcrypto.csv"),
       "esp80": csv(RES / "esp8266_80mhz.csv"), "esp160": csv(RES / "esp8266_160mhz.csv")}
compare("Mac BearSSL: rerun vs earlier", old["mac"], csv(NEW / "mac.csv"), tol=0.10)
compare("Mac libcrypto: rerun vs earlier", old["libcrypto"], csv(NEW / "mac_libcrypto.csv"), tol=0.10, floor_us=0.0)
if SCR:
    for clk, key in (("80", "bench"), ("160", "bench160")):
        A, B = raw(SCR / f"rr_{key}_A.raw"), raw(SCR / f"rr_{key}_B.raw")
        o = old[f"esp{clk}"]
        compare(f"ESP8266 @{clk} MHz board A (00d37d28): rerun vs earlier", o, A)
        compare(f"ESP8266 @{clk} MHz board B (00d377aa): vs earlier run of board A", o, B)
        compare(f"ESP8266 @{clk} MHz board A vs board B (same run)", A, B)
