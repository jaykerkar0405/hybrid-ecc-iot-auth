"""Deterministic common-environment cost model (no randomness).

Operation symbols: H hash, SE symmetric enc/dec (AEAD), ECM EC scalar mult, C extended chaotic map, fe fuzzy extractor, KDF session KDF.
A scheme is {role: {op: count}} with roles user/device/server, or {"total": {...}} when a paper gives only a combined cost (JIANG).
Constant sets: A = BASE Table III; B = each paper's own constants; C = our measured ESP8266 constants (research/paper_audit).
"""
import statistics as st
from common import T3, T4, T5, AUDIT, load_extracted
import reeval  # research/paper_audit/reeval.py: load(), pick(), constants()

KEYMAP = {"H": "H", "SE/D": "SE", "ECM": "ECM", "fe": "fe", "C": "C"}


def _conv(ops):
    return None if ops is None else {KEYMAP[k]: v for k, v in ops.items()}


# ---------------------------------------------------------------- proposed scheme readings (definitions from paper_audit/eq22_variants.py)
PROPOSED = {
    "V1 Table V as printed": {"device": {"H": 2, "SE": 2}, "server": {"H": 2, "SE": 2}},
    "V2 Table V + session KDF": {"device": {"H": 2, "SE": 2, "KDF": 1}, "server": {"H": 2, "SE": 2, "KDF": 1}},
    "V3 Eq.22 with AEAD": {"device": {"KDF": 1, "SE": 1}, "server": {"KDF": 1, "SE": 2}},
    "V4 2T_H = PID hash + KDF": {"device": {"H": 1, "KDF": 1, "SE": 2}, "server": {"H": 1, "KDF": 1, "SE": 2}},
}

# ---------------------------------------------------------------- competitor pools
def base_printed():
    """All nine BASE Table V competitors exactly as printed."""
    return {k: {r: _conv(v[r]) for r in ("user", "device", "server")} for k, v in T5.items() if k != "Proposed scheme"}


def jiang_published():
    """JIANG Table 2: online cost = P2 (login) + P3 (authentication); user+server combined, no role split (UNVERIFIED split)."""
    d = load_extracted()["ops"]["JIANG_table2"]["schemes"]["Jiang_ours"]
    return {"total": {"H": d["P2"]["TH"] + d["P3"]["TH"], "C": d["P2"]["TC"] + d["P3"]["TC"]}}


def jiang_p3_only():
    d = load_extracted()["ops"]["JIANG_table2"]["schemes"]["Jiang_ours"]
    return {"total": {"H": d["P3"]["TH"], "C": d["P3"]["TC"]}}


def changle_schemes():
    d = load_extracted()["ops"]
    out = {}
    for key, names in (("CHANGLE_table2", ("Li_11", "P1")), ("CHANGLE_table3", ("P2",))):
        for n in names:
            s = d[key]["schemes"][n]
            out["Chang-Le " + n if n == "P1" or n == "P2" else "Li et al. [CHANGLE 11]"] = {
                r: {k: v for k, v in {"H": s[role]["th"], "ECM": s[role].get("tmul", 0)}.items() if v}
                for r, role in (("user", "user"), ("device", "sensor"), ("server", "gateway"))}
    return out


def turkanovic_corrected():
    return {"user": {"H": 7}, "device": {"H": 5}, "server": {"H": 7}}  # CHANGLE Table II / DHILLON Table 3


def corrected_pool():
    """BASE pool with the two defects we can fix from the originals; rows whose source is unidentified are dropped, not guessed."""
    p = base_printed()
    p["Turkanovic [12]"] = turkanovic_corrected()
    p["Cheng-Le [14] (as CHANGLE P2)"] = changle_schemes()["Chang-Le P2"]
    del p["Cheng-Le [14]"]
    for k in ("Jiang [15]", "Shuai [16]"):   # source unidentified (findings F7/F8)
        del p[k]
    p["JIANG published (P2+P3)"] = jiang_published()
    return p


# ---------------------------------------------------------------- constants
def cost(ops, t):
    return 0.0 if not ops else sum(n * t[k] for k, n in ops.items())


def scheme_costs(s, t):
    """(user, device, server, dev+server, all) in ms; None where the paper gives no role split."""
    if "total" in s:
        c = cost(s["total"], t)
        return None, None, None, c, c
    u, d, v = (cost(s.get(r), t) for r in ("user", "device", "server"))
    return u, d, v, d + v, u + d + v


def const_A(kdf_ratio):
    return {"H": T3["H"], "SE": T3["SE/D"], "ECM": T3["ECM"], "C": T3["C"], "fe": T3["fe"], "KDF": kdf_ratio * T3["H"]}


def const_C(clock, aes="aes_big", T_C=None):
    rows = reeval.load(AUDIT / "results" / f"esp8266_{clock}mhz.csv")
    k = reeval.constants(rows, aes, "P-256 ec_p256_m15")
    t = {"H": k["H"], "SE": k["SE/D"], "ECM": k["ECM"], "fe": T3["fe"], "C": T3["C"] if T_C is None else T_C}  # fe: modelled (unmeasured)
    t["KDF"] = reeval.pick(rows, "HKDF-SHA256", "bearssl")
    return t


def measured_kdf_ratio(clock=80):
    t = const_C(clock)
    return t["KDF"] / t["H"]


def const_B():
    """Per-paper own constants. DHILLON gives none; hash-only rows without own constants borrow CHANGLE's t_h (flagged in outputs)."""
    k = load_extracted()["time_constants_ms"]
    ch, ji = k["CHANGLE"], k["JIANG"]
    return {
        "JIANG": {"H": ji["T_H"], "C": ji["T_C"]},
        "CHANGLE": {"H": ch["t_h"], "ECM": ch["t_mul"]},
    }


# ---------------------------------------------------------------- reductions (the definitions of paper_audit/audit.py that apply to a table)
def reductions(vals, prop):
    v = [x for x in vals.values() if x is not None]
    pct = lambda ref: 100 * (1 - prop / ref) if ref else float("nan")
    return {"vs best": pct(min(v)), "vs mean": pct(st.mean(v)), "vs median": pct(st.median(v)), "vs worst": pct(max(v))}


def rank_of(prop, vals):
    """1 = cheapest. Returns (rank, number of competitors cheaper than proposed)."""
    cheaper = sum(1 for x in vals.values() if x is not None and x < prop)
    return cheaper + 1, cheaper


def bits_pool(pool_names):
    out = {}
    for n in pool_names:
        if n in T4:
            out[n] = T4[n][4]
    return out


if __name__ == "__main__":
    print("kdf ratio (HKDF/T_H, ESP8266 80 MHz):", round(measured_kdf_ratio(), 2))
    print(const_C(80))
