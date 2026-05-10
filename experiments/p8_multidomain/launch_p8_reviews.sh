#!/bin/bash
set -e
cd "$(dirname "$0")/.."
LOG=p8_multidomain/_launch.log
: > $LOG

run_one() {
  local DOMAIN=$1
  local ROLE=$2
  local BID=$3
  local OUT="p8_multidomain/$DOMAIN/reviews/${ROLE}_${BID}.raw.txt"
  [ -s "$OUT" ] && return 0
  mkdir -p "$(dirname $OUT)"
  local PROMPT_FILE
  local CONTRACTS=""
  case $ROLE in
    cold)             PROMPT_FILE=p6_e2v2/prompts/cold_bankcheck.txt; CONTRACTS=p8_multidomain/$DOMAIN/contracts/contracts.md;;
    cold_mismatched)  PROMPT_FILE=p6_e2v2/prompts/cold_bankcheck.txt; CONTRACTS=p7_parser/contracts/parser_contracts.md;;
    warm)             PROMPT_FILE=t2/prompts/warm.txt;;
    skeptic)          PROMPT_FILE=t2/prompts/skeptic.txt;;
    *)                PROMPT_FILE=t2/prompts/generic.txt;;
  esac
  local B="p8_multidomain/$DOMAIN/bugged/${BID}.py"
  local TMP="/tmp/_p8_${DOMAIN}_${ROLE}_${BID}.txt"
  if [[ "$ROLE" == cold* ]]; then
    {
      cat $PROMPT_FILE | sed -e "/%CONTRACTS%/r $CONTRACTS" -e "/%CONTRACTS%/d"
      cat $B
    } > "$TMP"
  else
    {
      cat $PROMPT_FILE
      cat $B
    } > "$TMP"
  fi
  codex exec --skip-git-repo-check "$(cat $TMP)" > "$OUT" 2>&1
  echo "DONE $DOMAIN $ROLE $BID" >> $LOG
}

PAIRS=()
for DOMAIN in exprev regex httphdr; do
  for B in p8_multidomain/$DOMAIN/bugged/P8*.py; do
    BID=$(basename $B .py)
    for ROLE in cold cold_mismatched warm skeptic simm1 simm2 simm3; do
      OUT="p8_multidomain/$DOMAIN/reviews/${ROLE}_${BID}.raw.txt"
      [ -s "$OUT" ] && continue
      PAIRS+=("${DOMAIN}|${ROLE}|${BID}")
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
    DOMAIN="${P%%|*}"
    REST="${P#*|}"
    ROLE="${REST%|*}"
    BID="${REST#*|}"
    (run_one "$DOMAIN" "$ROLE" "$BID") &
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
  i=$((i + CHUNK))
done
echo "ALL_P8_DONE" >> $LOG
