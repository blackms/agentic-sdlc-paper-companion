#!/bin/bash
set -e
cd "$(dirname "$0")/.."
LOG=p5_e3/reviews/_launch_v2.log
: > $LOG

TEST_BUGS=$(python -c "import json; print('\n'.join(json.load(open('p5_e3/split.json'))['test']))")

PAIRS=()
for BID in $TEST_BUGS; do
  OUT="p5_e3/reviews/warm_injected_${BID}.raw.txt"
  [ -s "$OUT" ] && continue
  [ ! -s "t2/bugged/${BID}.py" ] && continue
  PAIRS+=("$BID")
done
echo "TOTAL E3 pairs: ${#PAIRS[@]}" >> $LOG

CHUNK=12
i=0
while [ $i -lt ${#PAIRS[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#PAIRS[@]}; j++)); do
    BID="${PAIRS[$((i+j))]}"
    {
      cat p5_e3/prompts/warm_injected.txt
      cat t2/bugged/${BID}.py
    } > /tmp/_p5e3v2_${BID}.txt
    (codex exec --skip-git-repo-check "$(cat /tmp/_p5e3v2_${BID}.txt)" > "p5_e3/reviews/warm_injected_${BID}.raw.txt" 2>&1
     echo "DONE warm_injected $BID" >> $LOG) &
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
  i=$((i + CHUNK))
  echo "Chunk done at i=$i" >> $LOG
done
echo "ALL_E3_V2_DONE" >> $LOG
