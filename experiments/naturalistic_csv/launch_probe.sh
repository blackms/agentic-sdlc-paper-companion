#!/bin/bash
# Naturalistic csv.py out-of-band leakage probe.
# After review, ask reviewer whether they've seen this exact bug/fix in the
# CPython issue tracker, and to cite an issue number if so.
# Same bugged sources, different prompt. 3 families × N bugs = 3N calls.
set -u
cd "$(dirname "$0")/.."  # to experiments/
LOG=naturalistic_csv/_launch.log
COND=probe

PROBE_SUFFIX='

# OUT-OF-BAND PROBE: This question is separate from the code review.
# Have you seen this exact bug or its fix in the Python CPython issue tracker?
# If yes, please cite the issue number. If no, write "NO".
# Answer in one line, e.g. "YES gh-12345" or "NO".
'

build_prompt() {
  local BID=$1
  cat naturalistic_csv/bugged/${BID}.py
  echo "$PROBE_SUFFIX"
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
    if [ "$sz" -lt 50 ]; then rm "$OUT"; else return 0; fi
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
