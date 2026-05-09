#!/bin/bash
set -e
cd "$(dirname "$0")/.."
mkdir -p p5_e3/reviews
LOG=p5_e3/reviews/_launch.log
: > $LOG

# Read TEST bugs from split.json
TEST_BUGS=$(python -c "import json; print('\n'.join(json.load(open('p5_e3/split.json'))['test']))")

for BID in $TEST_BUGS; do
  OUT="p5_e3/reviews/warm_injected_${BID}.raw.txt"
  [ -s "$OUT" ] && continue
  BUG_FILE="t2/bugged/${BID}.py"
  [ ! -s "$BUG_FILE" ] && { echo "missing $BUG_FILE" >> $LOG; continue; }
  {
    cat p5_e3/prompts/warm_injected.txt
    cat $BUG_FILE
  } > /tmp/_p5e3_${BID}.txt
  (codex exec --skip-git-repo-check "$(cat /tmp/_p5e3_${BID}.txt)" > "$OUT" 2>&1
   echo "DONE warm_injected $BID" >> $LOG) &
  [ $(jobs -r | wc -l) -ge 12 ] && wait -n
done
wait
echo "ALL_E3_CYCLE1_DONE" >> $LOG
