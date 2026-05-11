#!/bin/bash
# Naturalistic csv.py reviewer batch: cold-aligned condition.
# Three families run in parallel, each serial within itself (to avoid
# concurrent auth-refresh races on Codex ChatGPT subscription).
set -u
cd "$(dirname "$0")"
LOG=_launch.log
echo "START launch_cold $(date '+%F %T')" >> $LOG

bash _run_family.sh cold codex  > /tmp/_cold_codex.log  2>&1 < /dev/null &
PID_CX=$!
bash _run_family.sh cold opus   > /tmp/_cold_opus.log   2>&1 < /dev/null &
PID_OP=$!
bash _run_family.sh cold gemini > /tmp/_cold_gemini.log 2>&1 < /dev/null &
PID_GE=$!

wait $PID_CX $PID_OP $PID_GE
echo "END launch_cold $(date '+%F %T')" >> $LOG
