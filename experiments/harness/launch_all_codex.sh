#!/bin/bash
# Launch 12 codex runs in parallel: 2 tasks x 2 conditions x 3 runs.
set -e
mkdir -p runs
LOG=runs/launch.log
> $LOG
PIDS=()
for TASK in compound_interest transfer; do
  for COND in P0 P; do
    for RUN in 1 2 3; do
      (
        bash harness/run_codex.sh "$TASK" "$COND" "$RUN" >> "$LOG" 2>&1
        echo "DONE $TASK $COND $RUN" >> $LOG
      ) &
      PIDS+=($!)
    done
  done
done
echo "launched ${#PIDS[@]} pids"
echo "${PIDS[@]}" > runs/pids.txt
wait
echo "all done"
