#!/usr/bin/env bash
# Run INSIDE WSL. Usage: run_omnet.sh <path-to-research/reference_replication as seen from WSL> [main|sens|all]
# Compiles omnet/AuthNet.{ned,cc} against the OMNeT++ 6.0.3 build made by setup_toolchain_and_omnetpp.sh and runs every generated config.
set -e
SRC="$1"; WHICH="${2:-all}"
export PATH=~/opp-toolchain/bin:$PATH
. ~/omnetpp-6.0.3/setenv
rm -rf ~/authnet; mkdir -p ~/authnet
cp "$SRC"/omnet/AuthNet.ned "$SRC"/omnet/AuthNet.cc "$SRC"/omnet/omnetpp.ini "$SRC"/omnet/configs_main.txt "$SRC"/omnet/configs_sens.txt "$SRC"/omnet/configs_fig.txt "$SRC"/omnet/collect.py ~/authnet/
cd ~/authnet
opp_makemake -f --deep -o authnet -loppcommon -loppnedxml -loppscave -loppeventlog -lopplayout > /dev/null
make -j8 MODE=release 2>&1 | tail -3
LIST=""
[ "$WHICH" = main ] || LIST="$LIST $(cat configs_sens.txt)"
[ "$WHICH" = sens ] || LIST="$LIST $(cat configs_main.txt)"
[ "$WHICH" = all ] && LIST="$LIST $(cat configs_fig.txt)"
n=0
for c in $LIST; do
  ./authnet -u Cmdenv -c "$c" -f omnetpp.ini --result-dir=results > /dev/null
  n=$((n+1))
done
echo "ran $n configs"
python collect.py results > omnet_results.csv
wc -l omnet_results.csv
cp omnet_results.csv "$SRC"/results/omnet_results.csv
