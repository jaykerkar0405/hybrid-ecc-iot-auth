#!/usr/bin/env bash
# Run every ProVerif model and keep the full logs. Usage: ./run.sh [path-to-proverif]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
PV="${1:-${PROVERIF:-proverif}}"
mkdir -p logs
"$PV" -help 2>&1 | head -1 > logs/version.txt
run() { local f="$1"; shift; echo "== $f"; "$PV" "$@" "$f" > "logs/${f%.pv}.log" 2>&1 || true; grep -E "^RESULT|^Error|Observational equivalence" "logs/${f%.pv}.log" | sed 's/^/   /'; }
run auth.pv -lib common
run fs.pv -lib common
run unlink_counter.pv -lib common -lib unlink_common
run unlink_clock.pv -lib common -lib unlink_common
