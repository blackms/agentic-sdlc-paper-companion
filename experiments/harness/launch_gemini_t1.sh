#!/bin/bash
set -e
mkdir -p runs
LOG=runs/gemini_launch.log
> $LOG
for TASK in compound_interest transfer; do
  for COND in P0 P; do
    for RUN in 1 2 3 4 5; do
      OUT_PY="runs/gemini_${TASK}_${COND}_${RUN}.py"
      if [ ! -s "$OUT_PY" ]; then
        (
          gemini --model gemini-2.5-flash -p "$(cat prompts/${COND}_${TASK}.txt)" > "runs/gemini_${TASK}_${COND}_${RUN}.raw.txt" 2>&1
          python harness/extract_code.py "runs/gemini_${TASK}_${COND}_${RUN}.raw.txt" > "$OUT_PY"
          echo "DONE gemini $TASK $COND $RUN" >> $LOG
        ) &
      fi
    done
  done
done
wait
echo "ALL_GEMINI_DONE" >> $LOG
