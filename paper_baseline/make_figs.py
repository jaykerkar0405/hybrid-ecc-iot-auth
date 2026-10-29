#!/usr/bin/env python3
"""Figures for paper_baseline/main.tex. Every number is read from a repo file:
  - omnet_results_macos.csv / omnet_results_ext.csv  (OMNeT++ output)
  - published_baseline.json                          (Tables III-V of the base paper)
  - research/paper_audit/results/esp8266_{80,160}mhz.csv (primitive timings on the ESP8266)
Run: <venv>/bin/python -I paper_baseline/make_figs.py   (needs matplotlib)
"""
import csv, json, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "figs"
OUT.mkdir(exist_ok=True)
SIM = ROOT / "research/omnet_emulation/sim"
AUD = ROOT / "research/paper_audit/results"
pub = json.load(open(ROOT / "research/omnet_emulation/baseline/published_baseline.json"))
main = list(csv.DictReader(open(SIM / "omnet_results_macos.csv")))
ext = list(csv.DictReader(open(SIM / "omnet_results_ext.csv")))

# Okabe-Ito (colourblind-safe); identity is also carried by markers/hatching and labels
BLUE, ORANGE, GREEN, VERM, GREY, INK = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#8A8A8A", "#222222"
plt.rcParams.update({"font.size": 7.5, "font.family": "serif", "axes.edgecolor": "#555", "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e3e3e3",
                     "grid.linewidth": 0.5, "axes.axisbelow": True, "legend.frameon": False, "pdf.fonttype": 42})


def lat(rows, cfg, n=None):
    v = [float(r["latency_mean_ms"]) for r in rows if r["config"] == cfg and (n is None or int(r["N"]) == n)]
    return st.mean(v), min(v), max(v)


def bits(cfg):
    v = [float(r["kbit_on_air"]) * 1000 / float(r["sessions_completed"]) for r in ext if r["config"] == cfg]
    return st.mean(v)


def esp(csvname, op, variant=None, bytes_=None):
    """Rows are parsed from the right: a variant name such as aes_big(table,fast) contains an unquoted comma."""
    for line in open(AUD / csvname):
        p = line.rstrip("\n").split(",")
        if p[0] != "BENCH":
            continue
        o, v, b, med = p[2], ",".join(p[3:-8]), p[-8], p[-5]
        if o.startswith(op) and (variant is None or v.startswith(variant)) and (bytes_ is None or b == bytes_):
            return float(med) / 1000
    raise KeyError(op)


# ---- Fig. 1: communication bits, Table IV vs simulation ---------------------------------------------------------
sch = [("Proposed", "Proposed scheme", "AH_Proposed_V1_T4__BASE"), ("Porambage", "Poorambage [11]", "A_Poorambage__BASE"),
       ("Turkanović", "Turkanovic [12]", "A_Turkanovic_printed__BASE"), ("Dhillon–Kalra", "Dhillon-Karla [13]", "A_Dhillon_Karla__BASE"),
       ("Cheng–Le", "Cheng-Le [14]", "A_ChengLe_printed__BASE"), ("Jiang", "Jiang [15]", "A_Jiang15_printed__BASE"),
       ("Shuai", "Shuai [16]", "A_Shuai16_printed__BASE"), ("Wazid", "Wazid [17]", "A_Wazid__BASE"), ("Sadhukhan", "Sadhukhan [18]", "A_Sadhukhan__BASE")]
fig, ax = plt.subplots(figsize=(3.45, 2.55))
ys = list(range(len(sch)))[::-1]
for y, (lab, key, cfg) in zip(ys, sch):
    p, s = pub["table_IV_comm_bits"][key]["total"], bits(cfg)
    ax.barh(y + 0.19, p, height=0.34, color="white", edgecolor=BLUE if lab == "Proposed" else GREY, hatch="////", linewidth=0.6)
    ax.barh(y - 0.19, s, height=0.34, color=BLUE if lab == "Proposed" else GREY)
    ax.text(max(p, s) + 40, y, f"{s:.0f}", va="center", fontsize=6.5, color=INK)
ax.set_yticks(ys); ax.set_yticklabels([s[0] for s in sch]); ax.set_xlim(0, 3900)
ax.set_xlabel("bits per authentication session")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor="white", edgecolor=GREY, hatch="////", label="Table IV (published)"),
                   Patch(facecolor=GREY, label="simulated")], loc="lower right", fontsize=6.5)
ax.set_ylim(-1.5, len(sch) - 0.4)
ax.grid(axis="y", visible=False)
fig.tight_layout(pad=0.4); fig.savefig(OUT / "fig_bits.pdf"); plt.close(fig)

# ---- Fig. 2: primitive timings, Table III vs ESP8266 -----------------------------------------------------------
T3 = pub["table_III_ms"]
meas = {}
for tag, f in (("80", "esp8266_80mhz.csv"), ("160", "esp8266_160mhz.csv")):
    meas[tag] = {"$T_H$ (SHA-1)": esp(f, "T_H: SHA-1 (paper's T_H)", bytes_="32"),
                 "$T_{SE/D}$ (AES-GCM)": esp(f, "AES-GCM encrypt+tag (incl. key setup)", "aes_big(table,fast)/AES-256", "56"),
                 "$T_{ECM}$ (P-256)": esp(f, "T_ECM: scalar mult (variable base)", "P-256 ec_p256_m15")}
prim_json = {"table_III": T3, "esp8266_80MHz_ms": meas["80"], "esp8266_160MHz_ms": meas["160"]}
json.dump(prim_json, open(OUT / "primitives.json", "w"), indent=1)
labels = list(meas["80"])
paper_vals = [T3["H"], T3["SE/D"], T3["ECM"]]
fig, ax = plt.subplots(figsize=(3.45, 2.35))
w = 0.26
for i, (nm, vals, col, hatch) in enumerate((("Table III (reference)", paper_vals, "white", "////"),
                                          ("ESP8266, 80 MHz", list(meas["80"].values()), BLUE, None),
                                          ("ESP8266, 160 MHz", list(meas["160"].values()), ORANGE, None))):
    xs = [j + (i - 1) * w for j in range(3)]
    ax.bar(xs, vals, width=w * 0.92, color=col, edgecolor=GREY if hatch else col, hatch=hatch, linewidth=0.6, label=nm)
    for x, v in zip(xs, vals):
        ax.text(x, v * 1.25, f"{v:.3g}", ha="center", fontsize=5.2, color=INK)
ax.set_yscale("log"); ax.set_ylim(0.01, 1500); ax.set_xticks(range(3)); ax.set_xticklabels(labels)
ax.set_ylabel("time per operation (ms, log)"); ax.legend(loc="upper left", fontsize=6.3)
ax.grid(axis="x", visible=False)
fig.tight_layout(pad=0.4); fig.savefig(OUT / "fig_primitives.pdf"); plt.close(fig)

# ---- Fig. 3: device-side compute per handshake ---------------------------------------------------------------------
dev_t3 = 2 * T3["H"] + 2 * T3["SE/D"]
v1 = float(st.mean(float(r["latency_mean_ms"]) for r in ext if r["config"] == "AHM_Proposed_V1_T4__MEAS"))  # per session, ms
mea = {r["config"]: r for r in []}
import re
ini = (SIM / "omnetpp.ini").read_text()
def dev_ms(cfg):
    body = re.search(r"\[Config %s\]\n((?:(?!\[Config).*\n?)*)" % re.escape(cfg), ini).group(1)
    return float(re.search(r"deviceProcMs = ([\d.]+)", body).group(1))
bars = [("Table V\n× Table III", dev_t3, "white", "////"),
        ("Table V ×\nESP8266", dev_ms("M_Proposed_V1_T4__MEAS"), BLUE, None),
        ("+ session\nKDF", dev_ms("M_Proposed_V2_T4__MEAS"), BLUE, "\\\\\\\\"),
        ("firmware\nmeasured", 5.26, GREEN, None)]
fig, ax = plt.subplots(figsize=(3.45, 2.3))
for i, (lab, v, col, hatch) in enumerate(bars):
    ax.bar(i, v, width=0.62, color=col, edgecolor=GREY if col == "white" else (("white" if hatch else col)), hatch=hatch, linewidth=0.6)
    ax.text(i, v + 0.25, f"{v:.2f}", ha="center", fontsize=6.8, color=INK)
ax.set_xticks(range(4)); ax.set_xticklabels([b[0] for b in bars], fontsize=6.3)
ax.set_ylabel("device compute per handshake (ms)"); ax.set_ylim(0, 14)
ax.grid(axis="x", visible=False)
fig.tight_layout(pad=0.4); fig.savefig(OUT / "fig_device.pdf"); plt.close(fig)

# ---- Fig. 4: scalability -------------------------------------------------------------------------------------------
Ns = list(range(100, 1100, 100))
series = [("Table III constants, linear scan", main, "M_Proposed_V1_T4__BASE", VERM, "o", "-"),
          ("Table III constants, hash index", ext, "H_Proposed_V1_T4__BASE", VERM, "s", "--"),
          ("ESP8266 constants, linear scan", main, "M_Proposed_V1_T4__MEAS", BLUE, "o", "-"),
          ("ESP8266 constants, hash index", ext, "HM_Proposed_V1_T4__MEAS", BLUE, "s", "--")]
fig, ax = plt.subplots(figsize=(3.45, 2.55))
scal = {}
for lab, rows, cfg, col, mk, ls in series:
    m = [lat(rows, cfg, n) for n in Ns]
    scal[lab] = {"N": Ns, "mean_ms": [x[0] for x in m], "min_ms": [x[1] for x in m], "max_ms": [x[2] for x in m]}
    ax.plot(Ns, [x[0] for x in m], color=col, marker=mk, ms=3.2, lw=1.1, ls=ls, label=lab, markerfacecolor="white" if ls == "--" else col)
    ax.fill_between(Ns, [x[1] for x in m], [x[2] for x in m], color=col, alpha=0.12, lw=0)
json.dump(scal, open(OUT / "scalability.json", "w"), indent=1)
ax.set_yscale("log"); ax.set_xlabel("devices"); ax.set_ylabel("mean per-session latency (ms, log)")
ax.set_xlim(80, 1020); ax.set_ylim(1.5, 4e6); ax.legend(loc="upper left", fontsize=6.0)
fig.tight_layout(pad=0.4); fig.savefig(OUT / "fig_scale.pdf"); plt.close(fig)
print("wrote", sorted(p.name for p in OUT.iterdir()))
print("device-side:", [(b[0].replace(chr(10), ' '), round(b[1], 3)) for b in bars], "| ESP per-session V1 uncontended", round(v1, 3))
