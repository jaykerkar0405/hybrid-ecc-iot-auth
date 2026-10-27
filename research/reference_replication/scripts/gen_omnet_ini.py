#!/usr/bin/env python3
"""Generate omnet/omnetpp.ini from the paper tables.
Every scheme's per-session device/server delay and bit count comes from refmodel / BASE Tables III-V (nothing typed by hand).

Environments:
  BASE      BASE Table III constants (T_H = T_C = 0.32, T_SE/D = 5.6, T_ECM = 17.1, T_fe = 17.1 ms); KDF = measured ratio x T_H
  MEAS      our measured ESP8266 80 MHz constants for device and server
  MEAS_LAP  ESP8266 devices, laptop-class server (Mac BearSSL constants)
Main grid: every scheme x {BASE, MEAS}, N = 100..1000 step 100, 5 repetitions (seeds 0-4).
Sensitivity grid: the assumptions BASE does not fix (adversary share, arrival window, enrolment policy, range, server class,
JIANG device/server split, T_C, proposed message count), N = 100, 500, 1000.
"""
import sys
import refmodel as M
import step5_netsim as S5
from common import ROOT, T3, T4, T5

OUT = ROOT / "omnet" / "omnetpp.ini"
KDF_RATIO = M.measured_kdf_ratio(80)
NS_MAIN = "100,200,300,400,500,600,700,800,900,1000"
NS_SENS = "100,500,1000"
NS_FIG = "300,600,900,1200,1500,1800"   # x-axis of BASE Figs. 1-2 ("Vehicles in VANET")
SPEED_160KMH = 160 / 3.6                  # BASE Table II: device speed (max) 160 km/hour


def envs(tc=0.32):
    a = M.const_A(KDF_RATIO); a["C"] = tc
    dev, _ = S5.platform("esp8266_80mhz.csv", T_C=tc)
    srv_esp, tp_esp = S5.platform("esp8266_80mhz.csv", T_C=tc)
    srv_mac, tp_mac = S5.platform("mac.csv", T_C=tc)
    return {"BASE": (a, a, T3["H"], T3["H"]),
            "MEAS": (dev, srv_esp, tp_esp, srv_esp["H"]),
            "MEAS_LAP": (dev, srv_mac, tp_mac, srv_mac["H"])}


def schemes():
    """name -> (ops, total bits, number of messages, pseudonym lookup, source of bits)"""
    bp = M.base_printed()
    t4 = lambda k: T4[k][4]
    return {
        "Proposed_V1_T4": (M.PROPOSED["V1 Table V as printed"], 1024, 4, True, "BASE Table IV (4 msgs, 1024 bits)"),
        "Proposed_V2_T4": (M.PROPOSED["V2 Table V + session KDF"], 1024, 4, True, "BASE Table IV"),
        "Proposed_V1_text": (M.PROPOSED["V1 Table V as printed"], 264, 2, True, "BASE text Sec V-B / Eq. 21 (2 msgs, 264 bits)"),
        "Poorambage": (bp["Poorambage [11]"], t4("Poorambage [11]"), 4, False, "BASE Table IV"),
        "Turkanovic_printed": (bp["Turkanovic [12]"], t4("Turkanovic [12]"), 4, False, "BASE Table IV"),
        "Turkanovic_corrected": (M.turkanovic_corrected(), t4("Turkanovic [12]"), 4, False, "BASE Table IV"),
        "Dhillon_Karla": (bp["Dhillon-Karla [13]"], t4("Dhillon-Karla [13]"), 4, False, "BASE Table IV"),
        "ChengLe_printed": (bp["Cheng-Le [14]"], t4("Cheng-Le [14]"), 4, False, "BASE Table IV"),
        "ChengLe_as_P2": (M.changle_schemes()["Chang-Le P2"], t4("Cheng-Le [14]"), 4, False, "BASE Table IV (bits unverifiable)"),
        "Jiang15_printed": (bp["Jiang [15]"], t4("Jiang [15]"), 4, False, "BASE Table IV"),
        "Shuai16_printed": (bp["Shuai [16]"], t4("Shuai [16]"), 4, False, "BASE Table IV"),
        "Wazid": (bp["Wazid [17]"], t4("Wazid [17]"), 4, False, "BASE Table IV"),
        "Sadhukhan": (bp["Sadhukhan [18]"], t4("Sadhukhan [18]"), 4, False, "BASE Table IV"),
        "JIANG_published": (M.jiang_published(), 1312, 2, False, "JIANG Table 2 (2 rounds, 1312 bits)"),
        "ChangLe_P1": (M.changle_schemes()["Chang-Le P1"], t4("Cheng-Le [14]"), 4, False, "BASE Table IV Cheng-Le row (CHANGLE gives no sizes)"),
    }


def proc(ops, t, share=0.5):
    """(device_ms, server_ms). JIANG gives only a combined cost: split by `share` (UNVERIFIED)."""
    if "total" in ops:
        c = M.cost(ops["total"], t)
        return c * share, c * (1 - share)
    return M.cost(ops.get("device"), t), M.cost(ops.get("server"), t)


def section(name, extends, kv, comment=""):
    lines = [f"[Config {name}]"] + ([f"extends = {extends}"] if extends else []) + ([f"# {comment}"] if comment else [])
    lines += [f"{k} = {v}" for k, v in kv.items()]
    return "\n".join(lines) + "\n"


def core(**kw):
    return {f"*.core.{k}": v for k, v in kw.items()}


PAPERS_SCHEMES = ("Proposed_V1_T4", "Proposed_V2_T4", "Proposed_V1_text", "Turkanovic_corrected", "Dhillon_Karla", "ChengLe_as_P2", "ChangLe_P1", "JIANG_published")


def papers_env(sname):
    """Environment taken from the three papers: each scheme is costed with the constants of the paper it comes from.
    JIANG: T_H 0.20, T_C 32.40 ms. CHANGLE (P1, P2): t_mul 63.075, t_h 0.5 ms. DHILLON and Turkanovic give no times, so they borrow
    CHANGLE's t_h (flagged). The proposed scheme has no constants of its own and keeps BASE Table III."""
    k = M.const_B()
    a = M.const_A(KDF_RATIO)
    if sname == "JIANG_published":
        t = {"H": k["JIANG"]["H"], "C": k["JIANG"]["C"]}
    elif sname in ("ChengLe_as_P2", "ChangLe_P1"):
        t = {"H": k["CHANGLE"]["H"], "ECM": k["CHANGLE"]["ECM"]}
    elif sname in ("Dhillon_Karla", "Turkanovic_corrected"):
        t = {"H": k["CHANGLE"]["H"]}
    else:
        t = a
    return t, t, a["H"], t["H"]


def scheme_cfg(sname, env, tc=0.32, share=0.5):
    ops, bits, nmsg, lookup, _ = schemes()[sname]
    dt, st, probe, rej = papers_env(sname) if env == "PAPERS" else envs(tc)[env]
    if "total" in ops:
        c_dev = M.cost(ops["total"], dt); c_srv = M.cost(ops["total"], st)
        d, s = c_dev * share, c_srv * (1 - share)
    else:
        d, s = M.cost(ops.get("device"), dt), M.cost(ops.get("server"), st)
    return core(scheme=f'"{sname}"', bitsTotal=bits, nMessages=nmsg, deviceProcMs=f"{d:.6f}", serverProcMs=f"{s:.6f}",
                pseudonymLookup=str(lookup).lower(), tProbeMs=f"{probe:.6f}", rejectMs=f"{rej:.6f}")


def build():
    out = ["# GENERATED by scripts/gen_omnet_ini.py - do not edit. Re-run run_all.sh to regenerate.",
           "# Parameters follow BASE Table II unless marked ASSUMPTION.", "",
           "[General]", "network = AuthNet", "cmdenv-express-mode = true", "cmdenv-status-frequency = 1000s",
           "sim-time-limit = 1000s", "**.vector-recording = false", "**.param-recording = false",
           "repeat = 5", "seed-set = ${repetition}", "# BASE Table II", "*.core.rateBps = 10e6", "*.core.rangeM = 500",
           "*.core.quantumS = 15e-6", "*.core.handoffS = 10e-9", "*.core.txPowerW = 0.0756", "*.core.rxPowerW = 0.0756",
           "*.serverFraction = 0.05", "# ASSUMPTIONS (not in BASE)", "*.adversaryFraction = 0.05", "*.core.adversaryRateHz = 1",
           "*.core.windowS = 10", '*.core.enrolment = "reachable"', "*.core.windowEpochs = 13", ""]
    main = []
    for env in ("BASE", "MEAS", "PAPERS"):
        for sname, (_, _, _, _, src) in schemes().items():
            if env == "PAPERS" and sname not in PAPERS_SCHEMES:
                continue
            nm = f"M_{sname}__{env}"
            kv = {"*.numDevices": "${N=" + NS_MAIN + "}", **scheme_cfg(sname, env)}
            out.append(section(nm, None, kv, f"bits: {src}"))
            main.append(nm)
    sens = []

    def add_sens(tag, base_scheme, env, extra, tc=0.32, share=0.5):
        nm = f"S_{tag}".replace(".", "p")
        kv = {"*.numDevices": "${N=" + NS_SENS + "}", **scheme_cfg(base_scheme, env, tc, share), **extra}
        out.append(section(nm, None, kv)); sens.append(nm)

    for sname in ("Proposed_V1_T4", "Dhillon_Karla", "Sadhukhan"):
        for env in ("BASE", "MEAS"):
            for af in (0.0, 0.05, 0.10):
                add_sens(f"{sname}__{env}__adv{af}", sname, env, {"*.adversaryFraction": af})
            for w in (1, 10, 60):
                add_sens(f"{sname}__{env}__win{w}", sname, env, {"*.core.windowS": w})
            add_sens(f"{sname}__{env}__nearest", sname, env, {"*.core.enrolment": '"nearest"'})
            add_sens(f"{sname}__{env}__range800", sname, env, {"*.core.rangeM": 800})
    for sname in ("Proposed_V1_T4", "Proposed_V2_T4", "Dhillon_Karla"):
        add_sens(f"{sname}__MEAS_LAP", sname, "MEAS_LAP", {})
    for tc in (0.32, 32.40):
        for share in (0.0, 0.5, 1.0):
            for env in ("BASE", "MEAS"):
                add_sens(f"JIANG_published__{env}__Tc{tc}__devshare{share}", "JIANG_published", env, {}, tc, share)
    for sname in ("Proposed_V1_T4", "Dhillon_Karla", "Sadhukhan"):
        for env in ("BASE", "MEAS"):
            add_sens(f"{sname}__{env}__mobile160", sname, env, {"*.core.speedMps": f"{SPEED_160KMH:.4f}"})
    fig = []
    for sname, (_, _, _, _, src) in schemes().items():
        nm = f"F_{sname}__BASE"
        out.append(section(nm, None, {"*.numDevices": "${N=" + NS_FIG + "}", **scheme_cfg(sname, "BASE")}, "BASE Figs. 1-2 x-axis: 300..1800 devices"))
        fig.append(nm)
    (ROOT / "omnet" / "configs_fig.txt").write_text("\n".join(fig) + "\n", encoding="utf8", newline="\n")
    out.append("[Config ALL_MAIN]\n# placeholder (configs are run individually by run_omnet.sh)\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(out), encoding="utf8", newline="\n")
    (ROOT / "omnet" / "configs_main.txt").write_text("\n".join(main) + "\n", encoding="utf8", newline="\n")
    (ROOT / "omnet" / "configs_sens.txt").write_text("\n".join(sens) + "\n", encoding="utf8", newline="\n")
    print(f"wrote {OUT}: {len(main)} main configs (BASE, MEAS, PAPERS environments) x 50 runs, {len(sens)} sensitivity configs x 15 runs, {len(fig)} figure-axis configs x 30 runs")


if __name__ == "__main__":
    build()
