#!/bin/bash
# Naturalistic csv.py reviewer batch: cold-aligned condition.
# 3 families (codex, opus, gemini31) × N bugs × 1 condition (cold) = 3N calls.
# Resume-safe: skips outputs that are non-empty (>= 200 bytes for gemini).
set -u
cd "$(dirname "$0")/.."  # to experiments/
LOG=naturalistic_csv/_launch.log
COND=cold
CONTRACTS=p9_real/csv_dom/contracts/contracts.md

build_prompt() {
  # $1=BID
  local BID=$1
  sed -e "/%CONTRACTS%/r $CONTRACTS" -e "/%CONTRACTS%/d" p6_e2v2/prompts/cold_bankcheck.txt
  cat naturalistic_csv/bugged/${BID}.py
}

run_codex() {
  local BID=$1
  local OUT="naturalistic_csv/reviews/${COND}/codex_${BID}.raw.txt"
  if [ -s "$OUT" ]; then return 0; fi
  mkdir -p "$(dirname "$OUT")"
  local TMP="/tmp/_nat_cx_${COND}_${BID}.txt"
  build_prompt "$BID" > "$TMP"
  codex exec --skip-git-repo-check "$(cat "$TMP")" > "$OUT" 2>&1 || true
  echo "DONE_CX $COND $BID" >> $LOG
}

run_opus() {
  local BID=$1
  local OUT="naturalistic_csv/reviews/${COND}/opus_${BID}.raw.txt"
  if [ -s "$OUT" ]; then return 0; fi
  mkdir -p "$(dirname "$OUT")"
  local TMP="/tmp/_nat_op_${COND}_${BID}.txt"
  build_prompt "$BID" > "$TMP"
  cat "$TMP" | claude -p --model opus --output-format text > "$OUT" 2>&1 || true
  echo "DONE_OP $COND $BID" >> $LOG
}

run_gemini() {
  local BID=$1
  local OUT="naturalistic_csv/reviews/${COND}/gemini31_${BID}.raw.txt"
  if [ -s "$OUT" ]; then
    sz=$(wc -c < "$OUT")
    if [ "$sz" -lt 200 ]; then rm "$OUT"; else return 0; fi
  fi
  mkdir -p "$(dirname "$OUT")"
  local TMP="/tmp/_nat_ge_${COND}_${BID}.txt"
  build_prompt "$BID" > "$TMP"
  gemini -m "gemini-3.1-pro-preview" -p "$(cat "$TMP")" --approval-mode plan > "$OUT" 2>&1 || true
  echo "DONE_GE $COND $BID" >> $LOG
}

PAIRS=()
for B in naturalistic_csv/bugged/B*.py; do
  BID=$(basename "$B" .py)
  for FAM in codex opus gemini; do
    SUFFIX=$FAM
    [ "$FAM" = "gemini" ] && SUFFIX="gemini31"
    OUT="naturalistic_csv/reviews/${COND}/${SUFFIX}_${BID}.raw.txt"
    if [ ! -s "$OUT" ]; then
      PAIRS+=("${FAM}|${BID}")
    fi
  done
done
echo "TOTAL $COND: ${#PAIRS[@]}" >> $LOG

# Per-family CHUNK limits (cf. budget.md): opus<=6, gemini<=8, codex<=12.
# We run all families in one queue but max parallel = 6 (Opus floor).
CHUNK=6
i=0
while [ $i -lt ${#PAIRS[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#PAIRS[@]}; j++)); do
    P="${PAIRS[$((i+j))]}"
    FAM="${P%%|*}"
    BID="${P#*|}"
    case "$FAM" in
      codex)  run_codex  "$BID" & ;;
      opus)   run_opus   "$BID" & ;;
      gemini) run_gemini "$BID" & ;;
    esac
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do wait "$pid" 2>/dev/null; done
  echo "BATCH $COND i=$i" >> $LOG
  i=$((i + CHUNK))
done
echo "ALL_DONE $COND" >> $LOG
