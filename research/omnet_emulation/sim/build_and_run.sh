#!/usr/bin/env bash
# macOS build + run of the AuthNet model (OMNeT++ 6.4.0, headless). Usage: build_and_run.sh <config-list-file|config-name> [out-dir]
# Build happens in ./build (git-ignored); results go to ./results_macos (never over reference_replication/results).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
set +u; . "$HOME/opp/omnetpp-6.4.0/setenv" >/dev/null 2>&1; set -u
mkdir -p "$HERE/build" && cd "$HERE/build"
cp "$HERE"/AuthNet.ned "$HERE"/AuthNet.cc "$HERE"/omnetpp.ini "$HERE"/omnetpp_ext.ini .
[ -f Makefile ] || opp_makemake -f --deep -o authnet >/dev/null
make -j8 MODE=release 2>&1 | tail -3
ARG="${1:-}"; OUT="${2:-$HERE/results_macos}"
if [ -f "$HERE/$ARG" ]; then LIST="$(cat "$HERE/$ARG")"; else LIST="$ARG"; fi
for c in $LIST; do ./authnet -u Cmdenv -c "$c" -f omnetpp_ext.ini --result-dir="$OUT" >/dev/null; done
echo "done: $(echo $LIST | wc -w) configs -> $OUT"
