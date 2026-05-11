#!/bin/bash
# Helper: run one family serially across all bugs for one condition.
# Usage: ./_run_family.sh <cold|mismatched|probe> <codex|opus|gemini>
set -u
cd "$(dirname "$0")/.."  # to experiments/
COND=$1
FAM=$2
LOG=naturalistic_csv/_launch.log

# Contracts per condition
case "$COND" in
  cold)        CONTRACTS=p9_real/csv_dom/contracts/contracts.md ;;
  mismatched)  CONTRACTS=p6_e2v2/contracts/bankcheck_contracts.md ;;
  probe)       CONTRACTS="" ;;
  *) echo "bad cond"; exit 2 ;;
esac

build_prompt() {
  local BID=$1
  if [ "$COND" = "probe" ]; then
    cat naturalistic_csv/bugged/${BID}.py
    cat <<'EOF'

# OUT-OF-BAND PROBE: This question is separate from the code review.
# Have you seen this exact bug or its fix in the Python CPython issue tracker?
# If yes, please cite the issue number. If no, write "NO".
# Answer in one line, e.g. "YES gh-12345" or "NO".
EOF
  else
    sed -e "/%CONTRACTS%/r $CONTRACTS" -e "/%CONTRACTS%/d" p6_e2v2/prompts/cold_bankcheck.txt
    cat naturalistic_csv/bugged/${BID}.py
  fi
}

run_one() {
  local BID=$1
  local SUFFIX=$FAM
  [ "$FAM" = "gemini" ] && SUFFIX="gemini31"
  local OUT="naturalistic_csv/reviews/${COND}/${SUFFIX}_${BID}.raw.txt"
  if [ -s "$OUT" ]; then
    sz=$(wc -c < "$OUT")
    # For probe, accept smaller outputs (one-line answer)
    if [ "$COND" = "probe" ] && [ "$sz" -ge 5 ]; then return 0; fi
    if [ "$COND" != "probe" ] && tail -c 1500 "$OUT" 2>/dev/null | grep -qE '"verdict"|tokens used'; then return 0; fi
    rm -f "$OUT"
  fi
  mkdir -p "$(dirname "$OUT")"
  local TMP="/tmp/_nat_${FAM}_${COND}_${BID}.txt"
  build_prompt "$BID" > "$TMP"
  for attempt in 1 2 3; do
    case "$FAM" in
      codex)
        codex exec --skip-git-repo-check "$(cat "$TMP")" > "$OUT" 2>&1 < /dev/null || true
        ;;
      opus)
        cat "$TMP" | claude -p --model opus --output-format text > "$OUT" 2>&1 || true
        ;;
      gemini)
        gemini -m "gemini-3.1-pro-preview" -p "$(cat "$TMP")" --approval-mode plan > "$OUT" 2>&1 < /dev/null || true
        ;;
    esac
    sz=$(wc -c < "$OUT")
    # Acceptance: probe OK if >=5 bytes; review OK if has bugs_found JSON.
    if [ "$COND" = "probe" ]; then
      if [ "$sz" -ge 5 ]; then break; fi
    else
      if tail -c 1500 "$OUT" 2>/dev/null | grep -qE '"verdict"|tokens used'; then break; fi
    fi
    echo "RETRY_${FAM} $COND $BID attempt=$attempt size=$sz" >> $LOG
    sleep $((5 * attempt))
  done
  echo "DONE_${FAM} $COND $BID size=$(wc -c < "$OUT")" >> $LOG
}

# List bugs lacking a complete output for this family/condition.
BIDS=()
for B in naturalistic_csv/bugged/B*.py; do
  BID=$(basename "$B" .py)
  SUFFIX=$FAM
  [ "$FAM" = "gemini" ] && SUFFIX="gemini31"
  OUT="naturalistic_csv/reviews/${COND}/${SUFFIX}_${BID}.raw.txt"
  COMPLETE="no"
  if [ -s "$OUT" ]; then
    if [ "$COND" = "probe" ]; then
      [ "$(wc -c < "$OUT")" -ge 5 ] && COMPLETE="yes"
    else
      tail -c 1500 "$OUT" 2>/dev/null | grep -qE '"verdict"|tokens used' && COMPLETE="yes"
    fi
  fi
  if [ "$COMPLETE" = "no" ]; then BIDS+=("$BID"); fi
done
echo "FAM_TODO $FAM $COND: ${#BIDS[@]}" >> $LOG

for BID in "${BIDS[@]}"; do
  run_one "$BID"
done
echo "FAM_ALL_DONE $FAM $COND" >> $LOG
