#!/bin/bash
# Launch warm and skeptic Codex review for each bug.
set -e
cd "$(dirname "$0")"

mkdir -p reviews
LOG=reviews/_warm_skeptic.log
: > $LOG

for B in bugged/B*.py; do
  BID=$(basename $B .py)

  # WARM
  if [ ! -s "reviews/warm_${BID}.raw.txt" ]; then
    {
      cat prompts/warm.txt
      cat $B
    } > /tmp/_t2_warm_${BID}.txt
    (codex exec --skip-git-repo-check "$(cat /tmp/_t2_warm_${BID}.txt)" > "reviews/warm_${BID}.raw.txt" 2>&1
     echo "DONE warm $BID" >> $LOG) &
  fi

  # SKEPTIC
  if [ ! -s "reviews/skeptic_${BID}.raw.txt" ]; then
    {
      cat prompts/skeptic.txt
      cat $B
    } > /tmp/_t2_skeptic_${BID}.txt
    (codex exec --skip-git-repo-check "$(cat /tmp/_t2_skeptic_${BID}.txt)" > "reviews/skeptic_${BID}.raw.txt" 2>&1
     echo "DONE skeptic $BID" >> $LOG) &
  fi
done

wait
echo "ALL WARM+SKEPTIC DONE" >> $LOG
echo "OK"
