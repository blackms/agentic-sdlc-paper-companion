#!/bin/bash
# Launch T2 reviews via tmpfile (avoid arg length issues).
set -e
cd "$(dirname "$0")"

mkdir -p reviews
LOG=reviews/_launch.log
: > $LOG

for B in bugged/B*.py; do
  BID=$(basename $B .py)

  # COLD (cold contract-first via Codex)
  if [ ! -s "reviews/cold_${BID}.raw.txt" ]; then
    {
      cat prompts/cold.txt | sed -e "/%CONTRACTS%/r contracts/finance_contracts.md" -e "/%CONTRACTS%/d"
      cat $B
    } > /tmp/_t2_cold_${BID}.txt
    (codex exec --skip-git-repo-check "$(cat /tmp/_t2_cold_${BID}.txt)" > "reviews/cold_${BID}.raw.txt" 2>&1
     echo "DONE cold $BID" >> $LOG) &
  fi

  # SIMM (3× Codex generic)
  for K in 1 2 3; do
    if [ ! -s "reviews/simm${K}_${BID}.raw.txt" ]; then
      {
        cat prompts/generic.txt
        cat $B
      } > /tmp/_t2_simm${K}_${BID}.txt
      (codex exec --skip-git-repo-check "$(cat /tmp/_t2_simm${K}_${BID}.txt)" > "reviews/simm${K}_${BID}.raw.txt" 2>&1
       echo "DONE simm${K} $BID" >> $LOG) &
    fi
  done
done

wait
echo "ALL CODEX REVIEWS DONE" >> $LOG
echo "OK"
