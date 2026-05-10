#!/bin/bash
cd "$(dirname "$0")/.."
LOG=p9_real/_gem_jsondec.log

run_gemini() {
  local DOMAIN=$1
  local BID=$2
  local OUT="p9_real/$DOMAIN/reviews/cold_gemini31_${BID}.raw.txt"
  if [ -s "$OUT" ]; then
    sz=$(wc -c < "$OUT")
    if [ "$sz" -lt 200 ]; then rm "$OUT"; else return 0; fi
  fi
  local TMP="/tmp/_p9gem2_${DOMAIN}_${BID}.txt"
  {
    cat p6_e2v2/prompts/cold_bankcheck.txt | sed -e "/%CONTRACTS%/r p9_real/$DOMAIN/contracts/contracts.md" -e "/%CONTRACTS%/d"
    cat p9_real/$DOMAIN/bugged/${BID}.py
  } > "$TMP"
  gemini -m "gemini-3.1-pro-preview" -p "$(cat $TMP)" --approval-mode plan > "$OUT" 2>&1 || true
  echo "GEM_DONE $DOMAIN $BID" >> $LOG
}

PAIRS=()
for B in p9_real/jsondec_dom/bugged/P9j_B*.py; do
  BID=$(basename $B .py)
  OUT="p9_real/jsondec_dom/reviews/cold_gemini31_${BID}.raw.txt"
  if [ -s "$OUT" ]; then
    sz=$(wc -c < "$OUT")
    if [ "$sz" -lt 200 ]; then rm "$OUT"; PAIRS+=("$BID"); fi
  else
    PAIRS+=("$BID")
  fi
done
echo "TODO: ${#PAIRS[@]}" >> $LOG

# Smaller chunks to avoid quota throttling
CHUNK=4
i=0
while [ $i -lt ${#PAIRS[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#PAIRS[@]}; j++)); do
    BID="${PAIRS[$((i+j))]}"
    run_gemini jsondec_dom "$BID" &
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null
  done
  echo "BATCH i=$i" >> $LOG
  i=$((i + CHUNK))
  sleep 5
done
echo "ALL_GEM_JSON_DONE" >> $LOG
