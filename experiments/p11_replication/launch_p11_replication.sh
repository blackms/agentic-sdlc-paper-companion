#!/bin/bash
# P11 Replication launcher — Amendment A1 (saturation variant).
#
# Drives 226 paired Codex calls (53 csv unique * 2 conditions + 60 chardet
# unique * 2 conditions) over the frozen v1.3 cover stories and contracts.
# Interleaves truthful / relabeled per bug so reviewer drift is absorbed
# symmetrically. Resume-safe: any non-empty .raw.txt is skipped.
#
# Additionally re-runs the truthful condition on the 30 v1.3-reused bugs
# per side in a separate "drift_diagnostic" subdir (60 extra calls).
#
# Usage:
#   experiments/p11_replication/launch_p11_replication.sh [--drift-only]
#
# Output:
#   experiments/p11_replication/reviews/<side>_<cond>_<bid>.raw.txt
#   experiments/p11_replication/drift_diagnostic/<side>_truthful_v14_<bid>.raw.txt
#   experiments/p11_replication/_launch.log

cd "$(dirname "$0")/../.." || exit 1
ROOT="$(pwd)"
EXPDIR="experiments/p11_replication"
REVIEWS="$EXPDIR/reviews"
DRIFT="$EXPDIR/drift_diagnostic"
LOG="$EXPDIR/_launch.log"
SPEND="$EXPDIR/spend.md"
mkdir -p "$REVIEWS" "$DRIFT"

# Frozen v1.3 cover stories (byte-identical to experiments/p11_provenance/launch_p11.sh).
CSV_RELABEL="This code is from \`csv_processing\`, a niche third-party Python library for CSV manipulation (not part of the Python standard library). The library has approximately 500 downloads/month on PyPI. Treat this as unfamiliar third-party code."
CHARDET_RELABEL="This code is from \`charset_module\`, part of the Python standard library, available as \`from charset_module import ...\` since Python 3.10. Treat this as standard-library code."

# Truthful prefixes match v1.3 P11 baseline = NO cover prefix (the v1.3
# truthful condition was the bare cold_bankcheck prompt with no provenance
# line; see experiments/p11_provenance/launch_p11.sh which only added the
# relabeled cover, leaving truthful as the cold baseline). Per amendment
# §"What the amendment does NOT change", prompts are byte-identical to v1.3.
CSV_TRUTHFUL=""
CHARDET_TRUTHFUL=""

CSV_CONTRACTS="experiments/p9_real/csv_dom/contracts/contracts.md"
CHARDET_CONTRACTS="experiments/p10_thirdparty/chardet_dom/contracts/contracts.md"
COLD="experiments/p6_e2v2/prompts/cold_bankcheck.txt"

# Resolve bugged file: v13_reused uses the v1.3 bugged dir; v14_new uses our worktree bugged dir.
bugged_path_for() {
  local SIDE=$1 BID=$2 SOURCE=$3
  if [ "$SOURCE" = "v13_reused" ]; then
    if [ "$SIDE" = "csv" ]; then
      echo "experiments/p9_real/csv_dom/bugged/${BID}.py"
    else
      echo "experiments/p10_thirdparty/chardet_dom/bugged/${BID}.py"
    fi
  else
    if [ "$SIDE" = "csv" ]; then
      echo "$EXPDIR/bugged_csv/${BID}.py"
    else
      echo "$EXPDIR/bugged_chardet/${BID}.py"
    fi
  fi
}

build_prompt() {
  # $1=side $2=bid $3=condition (truthful|relabeled) $4=bugged_path
  local SIDE=$1 BID=$2 COND=$3 BUGGED=$4
  local COVER=""
  local CONTRACTS=""
  if [ "$SIDE" = "csv" ]; then
    CONTRACTS=$CSV_CONTRACTS
    [ "$COND" = "relabeled" ] && COVER="$CSV_RELABEL"
  else
    CONTRACTS=$CHARDET_CONTRACTS
    [ "$COND" = "relabeled" ] && COVER="$CHARDET_RELABEL"
  fi
  if [ -n "$COVER" ]; then
    printf "%s\n\n" "$COVER"
  fi
  # Splice contracts into the cold prompt at %CONTRACTS% marker.
  sed -e "/%CONTRACTS%/r $CONTRACTS" -e "/%CONTRACTS%/d" "$COLD"
  cat "$BUGGED"
}

run_one() {
  # $1=outpath  $2=side  $3=bid  $4=condition  $5=bugged_path
  local OUT=$1 SIDE=$2 BID=$3 COND=$4 BUGGED=$5
  if [ -s "$OUT" ]; then
    return 0
  fi
  local TMP
  TMP=$(mktemp -t p11rep.XXXXXX)
  build_prompt "$SIDE" "$BID" "$COND" "$BUGGED" > "$TMP"
  # Retry up to 3 times on auth-refresh / transient failure.
  local TRY
  for TRY in 1 2 3; do
    if cat "$TMP" | codex exec --skip-git-repo-check - > "$OUT" 2>&1; then
      # Require a JSON verdict to consider it a success.
      if grep -q '"verdict"' "$OUT" 2>/dev/null; then
        rm -f "$TMP"
        echo "DONE $SIDE $COND $BID try=$TRY" >> "$LOG"
        return 0
      fi
    fi
    sleep $((TRY * 5))
  done
  rm -f "$TMP"
  echo "FAIL $SIDE $COND $BID (3 retries)" >> "$LOG"
  return 1
}

# Build the work queue from manifest.json (interleave truthful then
# relabeled per bug to absorb reviewer drift symmetrically).
read_queue() {
  python3 experiments/p11_replication/_emit_queue.py main
}

read_drift_queue() {
  python3 experiments/p11_replication/_emit_queue.py drift
}

DRIFT_ONLY=0
if [ "${1:-}" = "--drift-only" ]; then
  DRIFT_ONLY=1
fi

CHUNK=12

echo "=== launch $(date -u +%FT%TZ) ===" >> "$LOG"

QUEUE=()
DRIFT_QUEUE=()

if [ "$DRIFT_ONLY" -eq 0 ]; then
  while IFS= read -r LINE; do
    QUEUE+=("$LINE")
  done < <(read_queue)
  echo "MAIN_QUEUE_SIZE=${#QUEUE[@]}" >> "$LOG"
  i=0
  while [ $i -lt ${#QUEUE[@]} ]; do
    PIDS=()
    for ((j=0; j<CHUNK && i+j<${#QUEUE[@]}; j++)); do
      ENTRY="${QUEUE[$((i+j))]}"
      IFS='|' read -r SIDE COND BID SRC BUGGED <<< "$ENTRY"
      OUT="$REVIEWS/${SIDE}_${COND}_${BID}.raw.txt"
      run_one "$OUT" "$SIDE" "$BID" "$COND" "$BUGGED" &
      PIDS+=($!)
    done
    for pid in "${PIDS[@]}"; do
      wait "$pid" 2>/dev/null
    done
    echo "BATCH main i=$i $(date -u +%FT%TZ)" >> "$LOG"
    i=$((i + CHUNK))
  done
fi

# Drift diagnostic: re-run truthful on the 30 v13_reused bugs per side.
while IFS= read -r LINE; do
  DRIFT_QUEUE+=("$LINE")
done < <(read_drift_queue)
echo "DRIFT_QUEUE_SIZE=${#DRIFT_QUEUE[@]}" >> "$LOG"
i=0
while [ $i -lt ${#DRIFT_QUEUE[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#DRIFT_QUEUE[@]}; j++)); do
    ENTRY="${DRIFT_QUEUE[$((i+j))]}"
    IFS='|' read -r SIDE COND BID SRC BUGGED <<< "$ENTRY"
    OUT="$DRIFT/${SIDE}_${COND}_${BID}.raw.txt"
    # Drift run uses truthful condition (no cover) regardless of label.
    run_one "$OUT" "$SIDE" "truthful" "$BID" "$BUGGED" &
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null
  done
  echo "BATCH drift i=$i $(date -u +%FT%TZ)" >> "$LOG"
  i=$((i + CHUNK))
done

# Update spend ledger (rough estimate: $0.30 per call mean per pre-reg budget.md).
N_MAIN=$(ls "$REVIEWS" 2>/dev/null | wc -l | tr -d ' ')
N_DRIFT=$(ls "$DRIFT" 2>/dev/null | wc -l | tr -d ' ')
TOTAL=$((N_MAIN + N_DRIFT))
PER_CALL_CENTS=30  # $0.30 estimate; refine post-hoc
SPEND_USD=$(python3 -c "print(f'{($TOTAL * $PER_CALL_CENTS) / 100.0:.2f}')")
{
  echo "# Spend (rough estimate)"
  echo
  echo "- main calls completed: $N_MAIN"
  echo "- drift calls completed: $N_DRIFT"
  echo "- estimated total: \$${SPEND_USD} at \$0.30/call"
} > "$SPEND"

echo "ALL_DONE $(date -u +%FT%TZ)" >> "$LOG"
