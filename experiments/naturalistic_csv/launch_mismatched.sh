#!/bin/bash
# Naturalistic csv.py reviewer batch: cold_mismatched condition.
set -u
cd "$(dirname "$0")"
LOG=_launch.log
echo "START launch_mismatched $(date '+%F %T')" >> $LOG

bash _run_family.sh mismatched codex  > /tmp/_mm_codex.log  2>&1 < /dev/null &
PID_CX=$!
bash _run_family.sh mismatched opus   > /tmp/_mm_opus.log   2>&1 < /dev/null &
PID_OP=$!
bash _run_family.sh mismatched gemini > /tmp/_mm_gemini.log 2>&1 < /dev/null &
PID_GE=$!

wait $PID_CX $PID_OP $PID_GE
echo "END launch_mismatched $(date '+%F %T')" >> $LOG
