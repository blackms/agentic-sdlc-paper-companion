#!/bin/bash
# Run cold_mismatched (bankcheck contracts on stdlib parser) for Opus + Gemini
# on csv_dom — closes the specificity-per-family methodological gap raised by Codex peer review.
cd "$(dirname "$0")/.."
LOG=p9_real/_mm_cf.log

build_prompt_mm() {
  local DOMAIN=$1
  local BID=$2
  cat p6_e2v2/prompts/cold_bankcheck.txt | sed -e "/%CONTRACTS%/r p6_e2v2/contracts/bankcheck_contracts.md" -e "/%CONTRACTS%/d"
  cat p9_real/$DOMAIN/bugged/${BID}.py
}

run_opus_mm() {
  local DOMAIN=$1
  local BID=$2
  local OUT="p9_real/$DOMAIN/reviews/cold_mismatched_opus_${BID}.raw.txt"
  if [ -s "$OUT" ]; then return 0; fi
  local TMP="/tmp/_p9opmm_${DOMAIN}_${BID}.txt"
  build_prompt_mm "$DOMAIN" "$BID" > "$TMP"
  cat "$TMP" | claude -p --model opus --output-format text > "$OUT" 2>&1 || true
  echo "MM_OPUS_DONE $DOMAIN $BID" >> $LOG
}

run_gemini_mm() {
  local DOMAIN=$1
  local BID=$2
  local OUT="p9_real/$DOMAIN/reviews/cold_mismatched_gemini31_${BID}.raw.txt"
  if [ -s "$OUT" ]; then
    sz=$(wc -c < "$OUT")
    if [ "$sz" -lt 200 ]; then rm "$OUT"; else return 0; fi
  fi
  local TMP="/tmp/_p9gemm_${DOMAIN}_${BID}.txt"
  build_prompt_mm "$DOMAIN" "$BID" > "$TMP"
  gemini -m "gemini-3.1-pro-preview" -p "$(cat $TMP)" --approval-mode plan > "$OUT" 2>&1 || true
  echo "MM_GEM_DONE $DOMAIN $BID" >> $LOG
}

PAIRS=()
for B in p9_real/csv_dom/bugged/P9c_B*.py; do
  BID=$(basename $B .py)
  for FAM in opus gemini; do
    OUT=""
    if [ "$FAM" = "opus" ]; then OUT="p9_real/csv_dom/reviews/cold_mismatched_opus_${BID}.raw.txt"; fi
    if [ "$FAM" = "gemini" ]; then OUT="p9_real/csv_dom/reviews/cold_mismatched_gemini31_${BID}.raw.txt"; fi
    if [ ! -s "$OUT" ]; then
      PAIRS+=("csv_dom|${FAM}|${BID}")
    fi
  done
done
echo "TOTAL_MM_CF: ${#PAIRS[@]}" >> $LOG

CHUNK=8
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
      run_opus_mm "$DOMAIN" "$BID" &
    elif [ "$FAM" = "gemini" ]; then
      run_gemini_mm "$DOMAIN" "$BID" &
    fi
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null
  done
  echo "BATCH i=$i" >> $LOG
  i=$((i + CHUNK))
done
echo "ALL_MM_CF_DONE" >> $LOG
