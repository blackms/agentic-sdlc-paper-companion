#!/bin/bash
set -e
cd "$(dirname "$0")/.."
LOG=p5_e2/reviews/_launch_v2.log
: > $LOG

run_one() {
  local ROLE=$1
  local BID=$2
  local OUT="p5_e2/reviews/${ROLE}_${BID}.raw.txt"
  [ -s "$OUT" ] && return 0
  local PROMPT_FILE
  case $ROLE in
    cold) PROMPT_FILE=t2/prompts/cold.txt;;
    warm) PROMPT_FILE=t2/prompts/warm.txt;;
    skeptic) PROMPT_FILE=t2/prompts/skeptic.txt;;
    *) PROMPT_FILE=t2/prompts/generic.txt;;
  esac
  local B="p5_e2/bugged/${BID}.py"
  local TMP="/tmp/_p5e2v2_${ROLE}_${BID}.txt"
  if [ "$ROLE" = "cold" ]; then
    {
      cat $PROMPT_FILE | sed -e "/%CONTRACTS%/r t2/contracts/finance_contracts.md" -e "/%CONTRACTS%/d"
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

export -f run_one
export LOG

# Build list of (role, bid) pairs to run
PAIRS=()
for B in p5_e2/bugged/E2_B*.py; do
  BID=$(basename $B .py)
  for ROLE in cold warm skeptic simm1 simm2 simm3; do
    OUT="p5_e2/reviews/${ROLE}_${BID}.raw.txt"
    [ -s "$OUT" ] && continue
    PAIRS+=("${ROLE}|${BID}")
  done
done
echo "TOTAL pairs to run: ${#PAIRS[@]}" >> $LOG

# Run in chunks of 12 parallel
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
  echo "Chunk done at i=$i" >> $LOG
done
echo "ALL_E2_V2_DONE" >> $LOG
