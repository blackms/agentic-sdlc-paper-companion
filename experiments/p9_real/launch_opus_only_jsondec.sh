#!/bin/bash
cd "$(dirname "$0")/.."
LOG=p9_real/_opus_only.log

run_opus() {
  local DOMAIN=$1
  local BID=$2
  local OUT="p9_real/$DOMAIN/reviews/cold_opus_${BID}.raw.txt"
  if [ -s "$OUT" ]; then return 0; fi
  local TMP="/tmp/_p9opus2_${DOMAIN}_${BID}.txt"
  {
    cat p6_e2v2/prompts/cold_bankcheck.txt | sed -e "/%CONTRACTS%/r p9_real/$DOMAIN/contracts/contracts.md" -e "/%CONTRACTS%/d"
    cat p9_real/$DOMAIN/bugged/${BID}.py
  } > "$TMP"
  cat "$TMP" | claude -p --model opus --output-format text > "$OUT" 2>&1 || true
  echo "OPUS_DONE $DOMAIN $BID" >> $LOG
}

PAIRS=()
for B in p9_real/jsondec_dom/bugged/P9j_B*.py; do
  BID=$(basename $B .py)
  if [ ! -s "p9_real/jsondec_dom/reviews/cold_opus_${BID}.raw.txt" ]; then
    PAIRS+=("$BID")
  fi
done
echo "TODO: ${#PAIRS[@]}" >> $LOG

CHUNK=8
i=0
while [ $i -lt ${#PAIRS[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#PAIRS[@]}; j++)); do
    BID="${PAIRS[$((i+j))]}"
    run_opus jsondec_dom "$BID" &
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null
  done
  echo "BATCH i=$i" >> $LOG
  i=$((i + CHUNK))
done
echo "ALL_DONE" >> $LOG
