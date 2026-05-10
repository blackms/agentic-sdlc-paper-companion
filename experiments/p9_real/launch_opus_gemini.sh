#!/bin/bash
# P9 reviewer-family extension: Opus 4.7 + Gemini 3.1 Pro Preview
# Targets: csv_dom + jsondec_dom (60 bugs each family = 120 total)
cd "$(dirname "$0")/.."
LOG=p9_real/_opus_gemini.log

build_prompt() {
  local DOMAIN=$1
  local BID=$2
  cat p6_e2v2/prompts/cold_bankcheck.txt | sed -e "/%CONTRACTS%/r p9_real/$DOMAIN/contracts/contracts.md" -e "/%CONTRACTS%/d"
  cat p9_real/$DOMAIN/bugged/${BID}.py
}

run_opus() {
  local DOMAIN=$1
  local BID=$2
  local OUT="p9_real/$DOMAIN/reviews/cold_opus_${BID}.raw.txt"
  if [ -s "$OUT" ]; then return 0; fi
  local TMP="/tmp/_p9opus_${DOMAIN}_${BID}.txt"
  build_prompt "$DOMAIN" "$BID" > "$TMP"
  cat "$TMP" | claude -p --model opus --output-format text > "$OUT" 2>&1 || true
  echo "DONE_OPUS $DOMAIN $BID" >> $LOG
}

run_gemini() {
  local DOMAIN=$1
  local BID=$2
  local OUT="p9_real/$DOMAIN/reviews/cold_gemini31_${BID}.raw.txt"
  if [ -s "$OUT" ]; then return 0; fi
  local TMP="/tmp/_p9gem_${DOMAIN}_${BID}.txt"
  build_prompt "$DOMAIN" "$BID" > "$TMP"
  gemini -m "gemini-3.1-pro-preview" -p "$(cat $TMP)" --approval-mode plan > "$OUT" 2>&1 || true
  echo "DONE_GEMINI $DOMAIN $BID" >> $LOG
}

PAIRS=()
for DOMAIN in csv_dom jsondec_dom; do
  for B in p9_real/$DOMAIN/bugged/P9*_B*.py; do
    BID=$(basename $B .py)
    OPUS_OUT="p9_real/$DOMAIN/reviews/cold_opus_${BID}.raw.txt"
    GEM_OUT="p9_real/$DOMAIN/reviews/cold_gemini31_${BID}.raw.txt"
    if [ ! -s "$OPUS_OUT" ]; then
      PAIRS+=("${DOMAIN}|opus|${BID}")
    fi
    if [ ! -s "$GEM_OUT" ]; then
      PAIRS+=("${DOMAIN}|gemini|${BID}")
    fi
  done
done
echo "TOTAL_RESUME: ${#PAIRS[@]}" >> $LOG

CHUNK=10
i=0
while [ $i -lt ${#PAIRS[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#PAIRS[@]}; j++)); do
    P="${PAIRS[$((i+j))]}"
    DOMAIN="${P%%|*}"
    REST="${P#*|}"
    FAM="${REST%|*}"
    BID="${REST#*|}"
    if [ "$FAM" = "opus" ]; then
      run_opus "$DOMAIN" "$BID" &
    elif [ "$FAM" = "gemini" ]; then
      run_gemini "$DOMAIN" "$BID" &
    fi
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null
  done
  echo "BATCH_DONE i=$i" >> $LOG
  i=$((i + CHUNK))
done
echo "ALL_OPUS_GEMINI_DONE" >> $LOG
