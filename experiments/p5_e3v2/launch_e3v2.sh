#!/bin/bash
# E3v2: warm Codex with CONCRETE-EXAMPLE injection on TEST set (101 bugs)
cd "$(dirname "$0")/.."
LOG=p5_e3v2/_launch.log
mkdir -p p5_e3v2/reviews

TEST_BUGS=$(python3 -c "import json; print('\n'.join(json.load(open('p5_e3/split.json'))['test']))")

PAIRS=()
for BID in $TEST_BUGS; do
  OUT="p5_e3v2/reviews/warm_injected_v2_${BID}.raw.txt"
  [ -s "$OUT" ] && continue
  [ ! -s "t2/bugged/${BID}.py" ] && continue
  PAIRS+=("$BID")
done
echo "TOTAL E3v2 pairs: ${#PAIRS[@]}" >> $LOG

run_one() {
  local BID=$1
  local OUT="p5_e3v2/reviews/warm_injected_v2_${BID}.raw.txt"
  local TMP="/tmp/_p5e3v2_${BID}.txt"
  {
    cat p5_e3v2/warm_injected_v2.txt
    cat t2/bugged/${BID}.py
  } > "$TMP"
  codex exec --skip-git-repo-check "$(cat $TMP)" > "$OUT" 2>&1 || true
  echo "DONE_E3v2 $BID" >> $LOG
}

CHUNK=12
i=0
while [ $i -lt ${#PAIRS[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#PAIRS[@]}; j++)); do
    BID="${PAIRS[$((i+j))]}"
    run_one "$BID" &
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null
  done
  echo "BATCH_DONE i=$i" >> $LOG
  i=$((i + CHUNK))
done
echo "ALL_E3v2_DONE" >> $LOG
