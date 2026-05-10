#!/bin/bash
# P10 reviewer batch: 3 domains × 30 bugs × 2 conditions × 3 families = 540 calls.
cd "$(dirname "$0")/.."
LOG=p10_thirdparty/_reviews.log

build_prompt() {
  # $1=domain $2=bid $3=condition (cold|cold_mismatched)
  local DOMAIN=$1; local BID=$2; local COND=$3
  if [ "$COND" = "cold" ]; then
    cat p6_e2v2/prompts/cold_bankcheck.txt | sed -e "/%CONTRACTS%/r p10_thirdparty/$DOMAIN/contracts/contracts.md" -e "/%CONTRACTS%/d"
  else
    cat p6_e2v2/prompts/cold_bankcheck.txt | sed -e "/%CONTRACTS%/r p6_e2v2/contracts/bankcheck_contracts.md" -e "/%CONTRACTS%/d"
  fi
  cat p10_thirdparty/$DOMAIN/bugged/${BID}.py
}

run_codex() {
  local DOMAIN=$1; local BID=$2; local COND=$3
  local OUT="p10_thirdparty/$DOMAIN/reviews/${COND}_codex_${BID}.raw.txt"
  if [ -s "$OUT" ]; then return 0; fi
  mkdir -p "$(dirname $OUT)"
  local TMP="/tmp/_p10cx_${DOMAIN}_${COND}_${BID}.txt"
  build_prompt "$DOMAIN" "$BID" "$COND" > "$TMP"
  codex exec --skip-git-repo-check "$(cat $TMP)" > "$OUT" 2>&1 || true
  echo "DONE_CX $DOMAIN $COND $BID" >> $LOG
}

run_opus() {
  local DOMAIN=$1; local BID=$2; local COND=$3
  local OUT="p10_thirdparty/$DOMAIN/reviews/${COND}_opus_${BID}.raw.txt"
  if [ -s "$OUT" ]; then return 0; fi
  mkdir -p "$(dirname $OUT)"
  local TMP="/tmp/_p10op_${DOMAIN}_${COND}_${BID}.txt"
  build_prompt "$DOMAIN" "$BID" "$COND" > "$TMP"
  cat "$TMP" | claude -p --model opus --output-format text > "$OUT" 2>&1 || true
  echo "DONE_OP $DOMAIN $COND $BID" >> $LOG
}

run_gemini() {
  local DOMAIN=$1; local BID=$2; local COND=$3
  local OUT="p10_thirdparty/$DOMAIN/reviews/${COND}_gemini31_${BID}.raw.txt"
  if [ -s "$OUT" ]; then
    sz=$(wc -c < "$OUT")
    if [ "$sz" -lt 200 ]; then rm "$OUT"; else return 0; fi
  fi
  mkdir -p "$(dirname $OUT)"
  local TMP="/tmp/_p10ge_${DOMAIN}_${COND}_${BID}.txt"
  build_prompt "$DOMAIN" "$BID" "$COND" > "$TMP"
  gemini -m "gemini-3.1-pro-preview" -p "$(cat $TMP)" --approval-mode plan > "$OUT" 2>&1 || true
  echo "DONE_GE $DOMAIN $COND $BID" >> $LOG
}

PAIRS=()
for DOMAIN in dateutil_dom parsy_dom chardet_dom; do
  for B in p10_thirdparty/$DOMAIN/bugged/P10*_B*.py; do
    BID=$(basename $B .py)
    for COND in cold cold_mismatched; do
      for FAM in codex opus gemini; do
        OUT_REL="p10_thirdparty/$DOMAIN/reviews/${COND}_${FAM}"
        if [ "$FAM" = "gemini" ]; then OUT_REL="${OUT_REL}31"; fi
        OUT="${OUT_REL}_${BID}.raw.txt"
        if [ ! -s "$OUT" ]; then
          PAIRS+=("${DOMAIN}|${COND}|${FAM}|${BID}")
        fi
      done
    done
  done
done
echo "TOTAL: ${#PAIRS[@]}" >> $LOG

CHUNK=12
i=0
while [ $i -lt ${#PAIRS[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#PAIRS[@]}; j++)); do
    P="${PAIRS[$((i+j))]}"
    DOMAIN="${P%%|*}"; R1="${P#*|}"
    COND="${R1%%|*}"; R2="${R1#*|}"
    FAM="${R2%%|*}"
    BID="${R2#*|}"
    case $FAM in
      codex)  run_codex  "$DOMAIN" "$BID" "$COND" & ;;
      opus)   run_opus   "$DOMAIN" "$BID" "$COND" & ;;
      gemini) run_gemini "$DOMAIN" "$BID" "$COND" & ;;
    esac
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null
  done
  echo "BATCH i=$i" >> $LOG
  i=$((i + CHUNK))
done
echo "ALL_P10_DONE" >> $LOG
