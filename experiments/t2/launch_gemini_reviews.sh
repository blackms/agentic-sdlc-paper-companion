#!/bin/bash
set -e
cd "$(dirname "$0")/.."
mkdir -p t2/reviews
LOG=t2/reviews/_gemini_launch.log
: > $LOG

for B in t2/bugged/B*.py; do
  BID=$(basename $B .py)
  if [ ! -s "t2/reviews/geminig_${BID}.raw.txt" ]; then
    {
      cat t2/prompts/generic.txt
      cat $B
    } > /tmp/_t2_geminig_${BID}.txt
    (gemini --model gemini-2.5-flash -p "$(cat /tmp/_t2_geminig_${BID}.txt)" > "t2/reviews/geminig_${BID}.raw.txt" 2>&1
     echo "DONE geminig $BID" >> $LOG) &
    # Throttle: 8 in flight max
    [ $(jobs -r | wc -l) -ge 8 ] && wait -n
  fi
done
wait
echo "ALL_GEMINI_DONE" >> $LOG
