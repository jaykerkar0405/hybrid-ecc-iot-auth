#!/usr/bin/env python3
"""Write omnetpp_ext.ini (includes omnetpp.ini) with the configs added for the baseline study:

  H_<proposed>__BASE   proposed scheme with a hash-indexed pseudonym lookup (pseudonymLookup = false: O(1) server resolve),
                       N = 100..1000 (main axis) and N = 300..1800 (Figs. 1-2 axis, as H_..._FIG)
  AH_<proposed>__BASE  same as A_ for the proposed scheme with a hash-indexed lookup (uncontended, no adversaries)
  A_<scheme>__BASE     every scheme in the main grid, BASE constants, NO adversaries, N = 100, one device each:
                       bits per session must equal BASE Table IV exactly; latency is the uncontended per-session cost.
The original configs are not modified. Parameters are copied from the existing sections, so nothing is retyped."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ini = (HERE / "omnetpp.ini").read_text(encoding="utf8")
secs = {m.group(1): m.group(0) for m in re.finditer(r"\[Config (\S+)\]\n(?:(?!\[Config).*\n?)*", ini)}
out = ["include omnetpp.ini", ""]
cfgs = {"H": [], "HF": [], "A": [], "AH": [], "HM": [], "AHM": []}

for name, body in secs.items():
    if name.startswith("M_Proposed") and name.endswith("__BASE"):
        s = name.replace("M_", "H_", 1)
        out.append(body.replace(f"[Config {name}]", f"[Config {s}]").replace("pseudonymLookup = true", "pseudonymLookup = false").rstrip() + "\n")
        cfgs["H"].append(s)
    if name.startswith("F_Proposed") and name.endswith("__BASE"):
        s = name.replace("F_", "HF_", 1)
        out.append(body.replace(f"[Config {name}]", f"[Config {s}]").replace("pseudonymLookup = true", "pseudonymLookup = false").rstrip() + "\n")
        cfgs["HF"].append(s)
    if name.startswith("M_Proposed") and name.endswith("__BASE"):
        s = name.replace("M_", "AH_", 1)
        b = re.sub(r"\*\.numDevices = .*", "*.numDevices = ${N=100}", body.replace(f"[Config {name}]", f"[Config {s}]"))
        out.append(b.replace("pseudonymLookup = true", "pseudonymLookup = false").rstrip() + "\n*.adversaryFraction = 0\n")
        cfgs["AH"].append(s)
    if name.startswith("M_Proposed") and name.endswith("__MEAS"):
        # measured ESP8266 80 MHz constants (device and server), hash-indexed lookup
        s = name.replace("M_", "HM_", 1)
        out.append(body.replace(f"[Config {name}]", f"[Config {s}]").replace("pseudonymLookup = true", "pseudonymLookup = false").rstrip() + "\n")
        cfgs["HM"].append(s)
        s = name.replace("M_", "AHM_", 1)
        b = re.sub(r"\*\.numDevices = .*", "*.numDevices = ${N=100}", body.replace(f"[Config {name}]", f"[Config {s}]"))
        out.append(b.replace("pseudonymLookup = true", "pseudonymLookup = false").rstrip() + "\n*.adversaryFraction = 0\n")
        cfgs["AHM"].append(s)
    if name.startswith("M_") and name.endswith("__BASE"):
        s = name.replace("M_", "A_", 1)
        b = re.sub(r"\*\.numDevices = .*", "*.numDevices = ${N=100}", body.replace(f"[Config {name}]", f"[Config {s}]"))
        out.append(b.rstrip() + "\n*.adversaryFraction = 0\n")
        cfgs["A"].append(s)

(HERE / "omnetpp_ext.ini").write_text("\n".join(out), encoding="utf8")
for k, v in cfgs.items():
    (HERE / f"configs_{k}.txt").write_text("\n".join(v) + "\n", encoding="utf8")
print({k: len(v) for k, v in cfgs.items()})
