#!/usr/bin/env bash
# Compile the model and run one config (smoke test). Usage (inside WSL): smoke.sh <path-to-research/reference_replication> <config>
set -e
SRC="$1"; CFG="${2:-M_Proposed_V1_T4__BASE}"
export PATH=~/opp-toolchain/bin:$PATH
. ~/omnetpp-6.0.3/setenv
rm -rf ~/authnet; mkdir -p ~/authnet
cp "$SRC"/omnet/AuthNet.ned "$SRC"/omnet/AuthNet.cc "$SRC"/omnet/omnetpp.ini "$SRC"/omnet/configs_main.txt "$SRC"/omnet/configs_sens.txt "$SRC"/omnet/configs_fig.txt "$SRC"/omnet/collect.py ~/authnet/
cd ~/authnet
opp_makemake -f --deep -o authnet -loppcommon -loppnedxml -loppscave -loppeventlog -lopplayout > /dev/null
make -j8 MODE=release 2>&1 | tail -15
time ./authnet -u Cmdenv -c "$CFG" -r 0,9 -f omnetpp.ini --result-dir=results_smoke | tail -5
python collect.py results_smoke
