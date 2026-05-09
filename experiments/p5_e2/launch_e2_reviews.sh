#!/bin/bash
set -e
cd "$(dirname "$0")/.."
mkdir -p p5_e2/reviews
LOG=p5_e2/reviews/_launch.log
: > $LOG

CONTRACTS_FILE=t2/contracts/finance_contracts.md
GEN_PROMPT=t2/prompts/generic.txt
WARM_PROMPT=t2/prompts/warm.txt
COLD_PROMPT=t2/prompts/cold.txt
SKEPTIC_PROMPT=t2/prompts/skeptic.txt

for B in p5_e2/bugged/E2_B*.py; do
  BID=$(basename $B .py)
  for ROLE in cold warm skeptic simm1 simm2 simm3; do
    OUT="p5_e2/reviews/${ROLE}_${BID}.raw.txt"
    [ -s "$OUT" ] && continue
    case $ROLE in
      cold) PROMPT_FILE=$COLD_PROMPT;;
      warm) PROMPT_FILE=$WARM_PROMPT;;
      skeptic) PROMPT_FILE=$SKEPTIC_PROMPT;;
      *) PROMPT_FILE=$GEN_PROMPT;;
    esac
    if [ "$ROLE" = "cold" ]; then
      {
        cat $PROMPT_FILE | sed -e "/%CONTRACTS%/r $CONTRACTS_FILE" -e "/%CONTRACTS%/d"
        cat $B
      } > /tmp/_p5e2_${ROLE}_${BID}.txt
    else
      {
        cat $PROMPT_FILE
        cat $B
      } > /tmp/_p5e2_${ROLE}_${BID}.txt
    fi
    (codex exec --skip-git-repo-check "$(cat /tmp/_p5e2_${ROLE}_${BID}.txt)" > "$OUT" 2>&1
     echo "DONE $ROLE $BID" >> $LOG) &
    [ $(jobs -r | wc -l) -ge 12 ] && wait -n
  done
done
wait
echo "ALL_E2_DONE" >> $LOG
