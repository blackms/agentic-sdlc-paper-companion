#!/bin/bash
set -e
cd "$(dirname "$0")/.."
LOG=p5_e2/reviews/_gemini_e2.log
: > $LOG

for B in p5_e2/bugged/E2_B*.py; do
  BID=$(basename $B .py)
  if [ ! -s "p5_e2/reviews/geminig_${BID}.raw.txt" ]; then
    {
      cat t2/prompts/generic.txt
      cat $B
    } > /tmp/_p5e2_gemini_${BID}.txt
    (gemini --model gemini-2.5-flash -p "$(cat /tmp/_p5e2_gemini_${BID}.txt)" > "p5_e2/reviews/geminig_${BID}.raw.txt" 2>&1
     echo "DONE geminig $BID" >> $LOG) &
    [ $(jobs -r | wc -l) -ge 6 ] && wait -n
  fi
done
wait
echo "ALL_GEMINI_E2_DONE" >> $LOG
