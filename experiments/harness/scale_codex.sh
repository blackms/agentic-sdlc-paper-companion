#!/bin/bash
set -e
mkdir -p runs
LOG=runs/scale.log
> $LOG
for TASK in compound_interest transfer; do
  for COND in P0 P; do
    for RUN in $(seq 4 15); do
      (
        if [ ! -s "runs/codex_${TASK}_${COND}_${RUN}.py" ]; then
          bash harness/run_codex.sh "$TASK" "$COND" "$RUN" >> "$LOG" 2>&1
          echo "DONE codex $TASK $COND $RUN" >> $LOG
        else
          echo "SKIP codex $TASK $COND $RUN (exists)" >> $LOG
        fi
      ) &
    done
  done
done
wait
echo "all-codex-scale-done"
