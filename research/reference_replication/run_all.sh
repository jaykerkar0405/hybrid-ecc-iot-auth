#!/usr/bin/env bash
# Regenerate everything under research/reference_replication from the PDFs and data files.
# Usage: bash research/reference_replication/run_all.sh        (from the repo root, Git Bash / Linux / macOS)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
if [ ! -d .venv ]; then python -m venv .venv; fi
PY=".venv/Scripts/python"; [ -x "$PY" ] || PY=".venv/bin/python"
"$PY" -m pip install -q -r requirements.txt
mkdir -p work/text work/png results
if command -v pdftotext >/dev/null 2>&1; then
  R="$(cd ../.. && pwd)"
  pdftotext -layout "$R/docs/references/base_paper.pdf" work/text/BASE.txt
  pdftotext -layout "$R/docs/references/chaotic_maps_three_factor_authentication.pdf" work/text/JIANG.txt
  pdftotext -layout "$R/docs/references/lightweight_biometrics_remote_user_authentication_for_iot.pdf" work/text/DHILLON.txt
  pdftotext -layout "$R/docs/references/provably_secure_authentication_for_ad_hoc_wsn.pdf" work/text/CHANGLE.txt
  pdftotext -layout "$R/paper/main.pdf" work/text/OURS.txt
fi
cd scripts
export PYTHONHASHSEED=0
"../$PY" -W ignore render_pages.py            > ../results/render_pages.log
"../$PY" -W ignore verify_pdf_text.py          # fails the run if a cited string is missing
"../$PY" -W ignore step2_reproduce.py          > ../results/step2_summary.txt
"../$PY" -W ignore step3_audit_base.py         > ../results/step3_summary.txt
"../$PY" -W ignore step4_common_env.py         > ../results/step4_summary.txt
"../$PY" -W ignore step5_netsim.py             > ../results/step5_summary.txt
"../$PY" -W ignore gen_omnet_ini.py            > ../results/gen_omnet_ini.log
# OMNeT++ 6.0.3 runs in WSL (set up once with omnet/setup_toolchain_and_omnetpp.sh). Without it the stored results/omnet_results.csv is used.
export MSYS_NO_PATHCONV=1
USE_STORED=1
if command -v wsl >/dev/null 2>&1 && wsl -d Ubuntu-22.04 -- bash -c 'test -x ~/omnetpp-6.0.3/bin/opp_run' >/dev/null 2>&1; then
  W="$(cd .. && pwd -W 2>/dev/null || pwd)"
  D="$(echo "${W:0:1}" | tr A-Z a-z)"; WSLROOT="/mnt/$D${W:2}"
  if wsl -d Ubuntu-22.04 -- bash -c "bash '$WSLROOT/omnet/run_omnet.sh' '$WSLROOT' all" > ../results/omnet_run.log 2>&1; then USE_STORED=0; fi
fi
if [ "$USE_STORED" = 1 ]; then echo "OMNeT++ run unavailable or failed (see results/omnet_run.log): using stored results/omnet_results.csv" | tee -a ../results/omnet_run.log; fi
"../$PY" -W ignore step5b_omnet_results.py     > ../results/step5b_summary.txt
"../$PY" -W ignore step7_base_vs_ours.py       > ../results/step7_summary.txt
"../$PY" -W ignore step6_compare_ours.py       > ../results/step6_summary.txt
"../$PY" -W ignore make_patch.py               > ../results/make_patch.log
"../$PY" -W ignore report_to_pdf.py            > ../results/report_to_pdf.log
cd ..
"$PY" -W ignore -m pytest -q tests
echo "done: see REPORT.md and results/"
