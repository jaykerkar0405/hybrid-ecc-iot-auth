#!/usr/bin/env python3
"""Collect OMNeT++ .sca result files into one CSV (one row per run). Run from the directory that holds results/."""
import csv
import re
import sys
from pathlib import Path

FIELDS = ["config", "N", "rep", "latency_mean_ms", "latency_p95_ms", "sessions_completed", "sessions_unreachable", "kbit_on_air",
          "energy_mJ", "end_time_s", "server_busy_total_ms", "server_busy_max_ms", "mean_enrolled_per_server", "n_servers"]


def parse(path):
    cfg, N, rep, core, busy, enrolled = None, None, None, {}, [], []
    for line in open(path, encoding="utf8", errors="replace"):
        if line.startswith("attr configname"):
            cfg = line.split()[2]
        elif line.startswith("attr iterationvars "):
            m = re.search(r"\$N=(\d+)", line)
            N = int(m.group(1)) if m else None
        elif line.startswith("attr repetition"):
            rep = int(line.split()[2])
        elif line.startswith("scalar "):
            _, mod, name, val = line.split()[:4]
            if mod.endswith(".core"):
                core[name] = float(val)
            elif ".servers[" in mod and name == "busy_ms":
                busy.append(float(val))
            elif ".servers[" in mod and name == "enrolled":
                enrolled.append(float(val))
    row = {"config": cfg, "N": N, "rep": rep, "server_busy_total_ms": sum(busy), "server_busy_max_ms": max(busy) if busy else 0,
           "mean_enrolled_per_server": sum(enrolled) / len(enrolled) if enrolled else 0, "n_servers": len(busy)}
    row.update({k: core.get(k, "") for k in FIELDS if k in core})
    return row


def main(d):
    rows = [parse(p) for p in sorted(Path(d).glob("*.sca"))]
    w = csv.DictWriter(sys.stdout, FIELDS, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in sorted(rows, key=lambda r: (r["config"], r["N"] or 0, r["rep"] or 0)):
        w.writerow(r)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results")
