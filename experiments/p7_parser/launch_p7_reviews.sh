#!/bin/bash
set -e
cd "$(dirname "$0")/.."
LOG=p7_parser/reviews/_launch.log
: > $LOG

run_one() {
  local ROLE=$1
  local BID=$2
  local OUT="p7_parser/reviews/${ROLE}_${BID}.raw.txt"
  [ -s "$OUT" ] && return 0
  local PROMPT_FILE
  case $ROLE in
    cold)             PROMPT_FILE=p6_e2v2/prompts/cold_bankcheck.txt; CONTRACTS_FILE=p7_parser/contracts/parser_contracts.md;;
    cold_mismatched)  PROMPT_FILE=p6_e2v2/prompts/cold_bankcheck.txt; CONTRACTS_FILE=p6_e2v2/contracts/bankcheck_contracts.md;;
    warm)             PROMPT_FILE=t2/prompts/warm.txt;;
    skeptic)          PROMPT_FILE=t2/prompts/skeptic.txt;;
    *)                PROMPT_FILE=t2/prompts/generic.txt;;
  esac
  local B="p7_parser/bugged/${BID}.py"
  local TMP="/tmp/_p7_${ROLE}_${BID}.txt"
  if [[ "$ROLE" == cold* ]]; then
    {
      cat $PROMPT_FILE | sed -e "/%CONTRACTS%/r $CONTRACTS_FILE" -e "/%CONTRACTS%/d"
      cat $B
    } > "$TMP"
  else
    {
      cat $PROMPT_FILE
      cat $B
    } > "$TMP"
  fi
  codex exec --skip-git-repo-check "$(cat $TMP)" > "$OUT" 2>&1
  echo "DONE $ROLE $BID" >> $LOG
}

PAIRS=()
for B in p7_parser/bugged/P7_B*.py; do
  BID=$(basename $B .py)
  for ROLE in cold cold_mismatched warm skeptic simm1 simm2 simm3; do
    OUT="p7_parser/reviews/${ROLE}_${BID}.raw.txt"
    [ -s "$OUT" ] && continue
    PAIRS+=("${ROLE}|${BID}")
  done
done
echo "TOTAL: ${#PAIRS[@]}" >> $LOG

CHUNK=12
i=0
while [ $i -lt ${#PAIRS[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#PAIRS[@]}; j++)); do
    PAIR="${PAIRS[$((i+j))]}"
    ROLE="${PAIR%|*}"
    BID="${PAIR#*|}"
    (run_one "$ROLE" "$BID") &
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
  i=$((i + CHUNK))
done
echo "ALL_P7_DONE" >> $LOG
