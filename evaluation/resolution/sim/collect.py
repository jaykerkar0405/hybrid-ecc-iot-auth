#!/usr/bin/env python3
# Copyright (c) 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur
# SPDX-License-Identifier: Apache-2.0
"""Parse the .sca files of the resolution sweep into one CSV row per run (stdlib only)."""
import csv, glob, re, sys
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
rows = []
for f in sorted(glob.glob(str(src / "*.sca"))):
    run = {"config": None, "N": None, "rep": None}
    core, servers = {}, {"enrolled": [], "state_bytes": [], "busy_ms": []}
    for line in open(f):
        if line.startswith("attr configname "):
            run["config"] = line.split()[2]
        elif line.startswith("itervar N "):
            run["N"] = int(line.split()[2])
        elif line.startswith("attr repetition "):
            run["rep"] = int(line.split()[2])
        elif line.startswith("scalar "):
            m = re.match(r"scalar (\S+) (\S+) (\S+)", line)
            mod, name, val = m.group(1), m.group(2), float(m.group(3))
            if mod.endswith(".core"):
                core[name] = val
            elif ".servers[" in mod and name in servers:
                servers[name].append(val)
    ns = len(servers["enrolled"]) or 1
    rows.append({**run, **{k: core.get(k, "") for k in ("latency_mean_ms", "latency_p95_ms", "sessions_completed",
                                                         "sessions_unreachable", "resolution_probes_total", "kbit_on_air")},
                 "n_servers": len(servers["enrolled"]), "mean_enrolled_per_server": sum(servers["enrolled"]) / ns,
                 "max_enrolled_per_server": max(servers["enrolled"] or [0]),
                 "mean_state_bytes_per_server": sum(servers["state_bytes"]) / ns,
                 "max_state_bytes_per_server": max(servers["state_bytes"] or [0]),
                 "server_busy_max_ms": max(servers["busy_ms"] or [0])})
rows.sort(key=lambda r: (r["config"], r["N"], r["rep"]))
with open(dst, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print(f"{len(rows)} runs -> {dst}")
