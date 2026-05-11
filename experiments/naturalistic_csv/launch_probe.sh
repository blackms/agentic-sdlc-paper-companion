#!/bin/bash
# Naturalistic csv.py reviewer batch: out-of-band leakage probe.
set -u
cd "$(dirname "$0")"
LOG=_launch.log
echo "START launch_probe $(date '+%F %T')" >> $LOG

bash _run_family.sh probe codex  > /tmp/_pb_codex.log  2>&1 < /dev/null &
PID_CX=$!
bash _run_family.sh probe opus   > /tmp/_pb_opus.log   2>&1 < /dev/null &
PID_OP=$!
bash _run_family.sh probe gemini > /tmp/_pb_gemini.log 2>&1 < /dev/null &
PID_GE=$!

wait $PID_CX $PID_OP $PID_GE
echo "END launch_probe $(date '+%F %T')" >> $LOG
