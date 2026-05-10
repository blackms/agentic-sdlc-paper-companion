#!/bin/bash
set -e
cd "$(dirname "$0")/.."
LOG=p6_e2v2/reviews/_cold_launch.log
: > $LOG

PAIRS=()
for B in p5_e2/bugged/E2_B*.py; do
  BID=$(basename $B .py)
  OUT="p6_e2v2/reviews/cold_${BID}.raw.txt"
  [ -s "$OUT" ] && continue
  PAIRS+=("$BID")
done
echo "TOTAL: ${#PAIRS[@]}" >> $LOG

CHUNK=8
i=0
while [ $i -lt ${#PAIRS[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#PAIRS[@]}; j++)); do
    BID="${PAIRS[$((i+j))]}"
    {
      cat p6_e2v2/prompts/cold_bankcheck.txt | sed -e "/%CONTRACTS%/r p6_e2v2/contracts/bankcheck_contracts.md" -e "/%CONTRACTS%/d"
      cat p5_e2/bugged/${BID}.py
    } > /tmp/_p6cold_${BID}.txt
    (codex exec --skip-git-repo-check "$(cat /tmp/_p6cold_${BID}.txt)" > "p6_e2v2/reviews/cold_${BID}.raw.txt" 2>&1
     echo "DONE cold $BID" >> $LOG) &
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
  i=$((i + CHUNK))
done
echo "ALL_COLD_DONE" >> $LOG
