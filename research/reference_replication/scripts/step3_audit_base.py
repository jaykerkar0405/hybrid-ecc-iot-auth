#!/usr/bin/env python3
"""Step 3: compare BASE's Tables IV/V rows with the original papers' numbers.
Each finding is tagged CONFIRMED / CONTRADICTED / UNVERIFIED and written to results/step3_findings.csv."""
from common import load_extracted, write_csv, RESULTS, T3, T4, T5


def th_counts(row):  # (user, device, server) T_H counts of a BASE Table V row
    return tuple((row[r] or {}).get("H", 0) for r in ("user", "device", "server"))


def build():
    d = load_extracted()
    F = []

    def add(fid, subject, tag, evidence):
        F.append((fid, subject, tag, evidence))

    # F1 Turkanovic
    b = th_counts(T5["Turkanovic [12]"])
    ch = d["ops"]["CHANGLE_table2"]["schemes"]["Turkanovic_1"]
    chv = (ch["user"]["th"], ch["sensor"]["th"], ch["gateway"]["th"])
    dh = d["ops"]["DHILLON_table3"]["schemes"]["Turkanovic_26"]
    dhv = (dh["user"]["Th"], dh["node"]["Th"], dh["gateway"]["Th"])
    tag = "CONTRADICTED" if (b[1], b[2]) == (dhv[2], dhv[1]) and chv == dhv else "CHECK"
    add("F1", "BASE Table V Turkanovic [12] device/server columns", tag,
        f"BASE (user,device,server) T_H = {b}; CHANGLE Table II (user,sensor,gateway) = {chv}; "
        f"DHILLON Table 3 (user,node,gateway) = {dhv}. Both originals agree and put 5 on the node and 7 on the gateway; "
        f"BASE has them swapped (device 7, server 5). Sum unchanged (19). Device column falls 7 -> 5 T_H, server rises 5 -> 7.")
    # F2 Dhillon
    b = th_counts(T5["Dhillon-Karla [13]"])
    p = d["ops"]["DHILLON_table3"]["schemes"]["Proposed"]
    pv = (p["user"]["Th"], p["node"]["Th"], p["gateway"]["Th"])
    add("F2", "BASE Table V Dhillon-Karla [13] counts", "CONFIRMED" if b == pv else "CONTRADICTED",
        f"BASE {b} vs DHILLON Table 3 proposed scheme {pv} (user, node, gateway).")
    add("F3", "BASE Table IV Dhillon-Karla [13] = 992/512/1024 = 2528 bits", "UNVERIFIED",
        "DHILLON gives no message-size table and no per-message bit counts; only 'hash value ... 128 bits' (Sec 5.2, p.266). "
        "The three-role sum cannot be traced to the paper.")
    # F4 Cheng-Le
    row = T5["Cheng-Le [14]"]
    b = th_counts(row)
    ecm = tuple((row[r] or {}).get("ECM", 0) for r in ("user", "device", "server"))
    p2 = d["ops"]["CHANGLE_table3"]["schemes"]["P2"]
    p2v = (p2["user"]["th"], p2["sensor"]["th"], p2["gateway"]["th"])
    p2e = (p2["user"]["tmul"], p2["sensor"]["tmul"], p2["gateway"]["tmul"])
    add("F4", "BASE Table V 'Cheng and Le [14]' vs CHANGLE P2", "CONTRADICTED (as printed); source identification UNVERIFIED",
        f"BASE T_H (user,device,server) = {b}, T_ECM = {ecm}. CHANGLE P2 (user,sensor,gateway) T_h = {p2v}, t_mul = {p2e}. "
        f"ECM counts and the device hash count match P2; BASE's user/server hash counts (9 / 7) equal P2's gateway/user counts (9 / 7) "
        f"exchanged between roles. Totals agree (21 hashes, 4 ECM). BASE's own reference [14] is Wang et al. (VANET), not Chang & Le, "
        f"so the row cannot have been taken from the cited source; P2 is the likely origin but BASE never says so.")
    add("F5", "BASE 'Cheng and Le [14]' reference", "CONFIRMED (mis-citation)",
        "BASE p.4491 ref [14] = C. Wang et al., 'A novel lightweight authentication protocol for emergency vehicle avoidance in VANETs', "
        "IEEE IoT J. 2021. Chang & Le (IEEE TWC 2016) is not in BASE's reference list.")
    add("F6", "BASE Table IV Cheng-Le [14] = 672/512/1088 = 2272 bits", "UNVERIFIED",
        "CHANGLE has four messages m1-m4 but no bit sizes or communication table.")
    # F7 Shuai / Jiang
    sh = T5["Shuai [16]"]
    add("F7", "BASE 'Shuai et al. [16]' row vs JIANG", "CONTRADICTED",
        f"BASE ref [16] is the Jiang et al. chaotic-maps paper (JIANG), but the row is costed {sh['user']}/{sh['device']}/{sh['server']} "
        f"with T_ECM in every role. JIANG uses no EC operation: P3 (authentication) = 7 T_H + 4 T_C, whole scheme 21 T_H + 6 T_C (Table 2). "
        f"The row does not correspond to JIANG; its true source is UNVERIFIED.")
    j = T5["Jiang [15]"]
    add("F8", "BASE 'Jiang et al. [15]' row", "UNVERIFIED",
        f"BASE ref [15] is Wen et al., 'Integrated sensing-communication-computation for edge AI' (IEEE IoT Mag. 2024), not an authentication scheme. "
        f"Row = {j['user']}/{j['device']}/{j['server']} T_H. No (7,5,10) row appears in JIANG, DHILLON Table 3 or CHANGLE Tables II-III. Source undetermined.")
    # F9 T_C
    TH = d["time_constants_ms"]["JIANG"]["T_H"]
    TC = d["time_constants_ms"]["JIANG"]["T_C"]
    add("F9", "BASE Table III T_C = 0.32 ms vs JIANG T_C = 32.40 ms", "CONTRADICTED",
        f"BASE sets T_C = T_H = 0.32 ms (ratio 1). JIANG: T_H = {TH} ms, T_C = {TC} ms (ratio {TC/TH:.0f}); BASE's T_C is {TC/T3['C']:.0f}x below JIANG's. "
        f"BASE Table V uses no T_C, so the constant is inert in BASE's own numbers; it matters only if a chaotic-map scheme is costed as published.")
    j3 = 11 * 0.32
    add("F10", "JIANG P3 and whole-scheme time under BASE vs JIANG constants", "CONFIRMED (computed)",
        f"P3 = 7 T_H + 4 T_C: BASE constants {j3:.2f} ms, JIANG's {7*TH+4*TC:.1f} ms ({(7*TH+4*TC)/j3:.0f}x). "
        f"Whole scheme 21 T_H + 6 T_C: BASE constants {27*0.32:.2f} ms, JIANG's {21*TH+6*TC:.1f} ms. "
        f"Printed time (TC ~32.40 ms) is in JIANG p.15 Sec 7, not 0.32 ms.")
    add("F11", "BASE Table IV Jiang [15] 1952 / Shuai [16] 2368 bits vs JIANG's 1312/1584", "CONTRADICTED",
        "JIANG Table 2: 1312 bits for its scheme (2 rounds), 1584 (Lee-Hsu, 3 rounds), 1312 (Islam, 2 rounds). Neither BASE row equals them, "
        "and BASE lists 4 messages for every scheme while JIANG has 2 rounds. The origin of 1312 is itself not derivable from JIANG's text (UNVERIFIED).")
    bad = [k for k, (m, u, dv, s, t) in T4.items() if (u or 0) + dv + s != t]
    add("F12", "BASE Table IV: Total = user + device + server", "CONFIRMED" if not bad else "CONTRADICTED",
        f"mismatching rows: {bad or 'none'}. All rows list 4 messages.")
    add("F13", "OURS classifies 'Jiang' as a hash-only scheme (OURS Sec IV-C, Table II; OURS ref [5] = JIANG)", "CONTRADICTED",
        "OURS ref [5] is the Jiang chaotic-maps paper, which per its Table 2 needs 6 extended-chaotic-map operations (T_C) per run, so it is not hash-only. "
        "The hash-only reading holds only for BASE's row 'Jiang [15]' (7/5/10 T_H), whose source is unidentified (F8) and which does not correspond to OURS ref [5]. "
        "OURS's operation counts for 'Jiang' are BASE's, not JIANG's.")
    add("F14", "Turkanovic and Dhillon-Karla as hash-only", "CONFIRMED",
        "Both are hash/XOR-only in their originals (CHANGLE Table II, DHILLON Table 3). Turkanovic's device/server split is swapped in BASE (F1) but totals are right.")
    e = d["base_table2_environment"]
    add("F15", "BASE Table II environment internal consistency", "CONFIRMED (inconsistencies)",
        f"'Server {e['servers']}': 5% of N is one per 20 devices, not one per 100 (=1%). 'Packet Size {e['packet_size']}' is a rate; the text says 128 bits/message. "
        f"'device Speed (Max) {e['device_speed_max']}' and 'Hand-off Time' conflict with static devices (Sec V).")
    return F


def main():
    F = build()
    write_csv(RESULTS / "step3_findings.csv", ["id", "subject", "tag", "evidence"], F)
    for f in F:
        print(f"[{f[0]}] {f[2]:45s} {f[1]}\n      {f[3]}\n")


if __name__ == "__main__":
    main()
