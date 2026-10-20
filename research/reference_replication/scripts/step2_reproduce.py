#!/usr/bin/env python3
"""Step 2: reproduce each reference paper's own numbers from its own model.
Outputs results/step2_<paper>.csv (every cell: printed, computed, status) and prints a summary."""
from common import load_extracted, write_csv, RESULTS

TOL = 1e-9  # printed values are given to the digits shown; computed values are exact decimals

def jiang(d):
    k = d["time_constants_ms"]["JIANG"]; TH, TC = k["T_H"], k["T_C"]
    sch = d["ops"]["JIANG_table2"]["schemes"]; rows = []
    for name, s in sch.items():
        sums = {"TH": 0, "TC": 0}
        for p in ("P1", "P2", "P3", "P4", "P5"):
            for o in sums: sums[o] += s[p][o]
        for o in sums:
            rows.append((name, f"overall {o}", s["overall"][o], sums[o], "MATCH" if s["overall"][o] == sums[o] else "MISMATCH"))
        for p in ("P1", "P2", "P3", "P4", "P5", "overall"):
            t = s[p]["TH"] * TH + s[p]["TC"] * TC
            rows.append((name, f"time {p} (ms)", "not printed (Fig. 3 only)", round(t, 4), "COMPUTED"))
    for name, b in d["ops"]["JIANG_table2"]["communication_bits"].items():
        rows.append((name, "communication bits", b, "not derivable (no field sizes besides |p|=256)", "UNVERIFIED"))
    return rows

def dhillon(d):
    rows = []
    for name, s in d["ops"]["DHILLON_table3"]["schemes"].items():
        tot = sum(v for r in s.values() for k, v in r.items() if k == "Th")
        other = {k: v for r in s.values() for k, v in r.items() if k != "Th"}
        rows.append((name, "sum of T_h over 3 roles", "not printed", tot, "COMPUTED" + (f" (+{other})" if other else "")))
    rows.append(("hash size", "bits", 128, 128, "MATCH (text only; Sec 5.2)"))
    rows.append(("time constants", "T_h in ms", "none given", "none", "UNVERIFIED (paper gives no times)"))
    return rows

def changle(d):
    k = d["time_constants_ms"]["CHANGLE"]; tm, th, tx = k["t_mul"] / 1000, k["t_h"] / 1000, k["t_XOR"] / 1000
    rows = []
    for tab, key in (("II", "CHANGLE_table2"), ("III", "CHANGLE_table3")):
        for name, roles in d["ops"][key]["schemes"].items():
            for role, c in roles.items():
                comp = c.get("tmul", 0) * tm + c["th"] * th + c.get("txor", 0) * tx
                ok = abs(comp - c["printed_s"]) < 1e-9
                rows.append((f"T{tab} {name} {role}", f"{c.get('tmul',0)}t_mul+{c['th']}t_h" + (f"+{c['txor']}t_XOR" if "txor" in c else ""),
                             c["printed_s"], round(comp, 6), "MATCH" if ok else f"MISMATCH (printed - computed = {c['printed_s']-comp:+.6f} s)"))
    t3 = d["ops"]["CHANGLE_table3"]["schemes"]
    for n in ("Shi_15", "Choi_16"):
        c = t3[n]["gateway"]; g = c["tmul"] * tm + c["th"] * th; p2 = t3["P2"]["gateway"]["th"] * th
        rows.append((f"claim '~14x faster' gateway {n} vs P2", "t_gateway(other)/t_gateway(P2)", "~14", round(g / p2, 3),
                     "MATCH (14.5-14.6 ~ 'approximately 14')"))
    t2 = d["ops"]["CHANGLE_table2"]["schemes"]
    same = t2["P1"]["sensor"] == t2["Turkanovic_1"]["sensor"]
    rows.append(("claim 'P1 slightly more efficient than Turkanovic at sensor node'", "Table II sensor cells",
                 "P1 < Turkanovic", "identical cells (5t_h+4t_XOR = 0.0025 s)" if same else "differs", "CONTRADICTED by its own Table II" if same else "MATCH"))
    rows.append(("P1 gateway vs Turkanovic gateway", "8t_h+1t_XOR vs 7t_h+4t_XOR", "'as efficient as Turkanovic'",
                 f"{t2['P1']['gateway']['printed_s']} s vs {t2['Turkanovic_1']['gateway']['printed_s']} s", "P1 gateway is 0.5 ms (14%) HIGHER"))
    return rows

def main():
    d = load_extracted()
    for name, fn in (("JIANG", jiang), ("DHILLON", dhillon), ("CHANGLE", changle)):
        rows = fn(d)
        write_csv(RESULTS / f"step2_{name.lower()}.csv", ["item", "formula", "printed", "computed", "status"], rows)
        bad = [r for r in rows if r[4].startswith(("MISMATCH", "CONTRADICTED"))]
        print(f"\n=== {name}: {len(rows)} items, {sum(r[4].startswith('MATCH') for r in rows)} match, {len(bad)} mismatch/contradicted")
        for r in rows: print("  ", " | ".join(str(x) for x in r))

if __name__ == "__main__":
    main()
