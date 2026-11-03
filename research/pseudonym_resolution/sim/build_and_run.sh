#!/usr/bin/env bash
# Build and run the pseudonym-resolution sweep (OMNeT++ 6.4.0, headless Cmdenv), then collect results.csv.
# Needs ../cost_model.csv (run ../resolution_costs.py first). Build goes to ./build (git-ignored).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
set +u; . "$HOME/opp/omnetpp-6.4.0/setenv" >/dev/null 2>&1; set -u
mkdir -p "$HERE/build" && cd "$HERE/build"
cp "$HERE"/ResolveNet.ned "$HERE"/ResolveNet.cc "$HERE"/omnetpp.ini .
[ -f Makefile ] || opp_makemake -f --deep -o resolvenet >/dev/null
make -j8 MODE=release 2>&1 | tail -2
rm -rf "$HERE/build/results"
for c in R_none R_O1 R_O2 R_O3 R_O4 R_TM R_CR R_MW H_none H_O1 H_O2 H_O3 H_O4 H_TM H_CR H_MW; do
  ./resolvenet -u Cmdenv -c "$c" -f omnetpp.ini --result-dir="$HERE/build/results" >/dev/null &
done
wait
{ opp_run -v 2>/dev/null || true; } | head -1 > "$HERE/omnet_version.txt" || true
python3 "$HERE/collect.py" "$HERE/build/results" "$HERE/results.csv"
