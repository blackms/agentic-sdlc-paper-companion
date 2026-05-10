#!/bin/bash
# P11 provenance-label experiment: relabel csv (stdlib→third-party)
# and chardet (third-party→stdlib). 60 Codex calls total.
cd "$(dirname "$0")/.."
LOG=p11_provenance/_launch.log

# Cover stories prepended to the cold prompt before contracts
CSV_RELABEL="This code is from \`csv_processing\`, a niche third-party Python library for CSV manipulation (not part of the Python standard library). The library has approximately 500 downloads/month on PyPI. Treat this as unfamiliar third-party code."
CHARDET_RELABEL="This code is from \`charset_module\`, part of the Python standard library, available as \`from charset_module import ...\` since Python 3.10. Treat this as standard-library code."

build_prompt() {
  # $1=domain $2=bid $3=contracts $4=cover_story $5=bugged_path
  local DOMAIN=$1; local BID=$2; local CONTRACTS=$3; local COVER=$4; local BUGGED=$5
  echo "$COVER"
  echo
  cat p6_e2v2/prompts/cold_bankcheck.txt | sed -e "/%CONTRACTS%/r $CONTRACTS" -e "/%CONTRACTS%/d"
  cat "$BUGGED"
}

run_one() {
  local BID=$1
  local TAG=$2  # csv_relabel_thirdparty | chardet_relabel_stdlib
  local OUT="p11_provenance/reviews/${TAG}_${BID}.raw.txt"
  if [ -s "$OUT" ]; then return 0; fi
  local TMP="/tmp/_p11_${TAG}_${BID}.txt"
  if [ "$TAG" = "csv_relabel_thirdparty" ]; then
    build_prompt "csv_dom" "$BID" "p9_real/csv_dom/contracts/contracts.md" "$CSV_RELABEL" "p9_real/csv_dom/bugged/${BID}.py" > "$TMP"
  else
    build_prompt "chardet_dom" "$BID" "p10_thirdparty/chardet_dom/contracts/contracts.md" "$CHARDET_RELABEL" "p10_thirdparty/chardet_dom/bugged/${BID}.py" > "$TMP"
  fi
  codex exec --skip-git-repo-check "$(cat $TMP)" > "$OUT" 2>&1 || true
  echo "DONE $TAG $BID" >> $LOG
}

PAIRS=()
for B in p9_real/csv_dom/bugged/P9c_B*.py; do
  BID=$(basename $B .py)
  if [ ! -s "p11_provenance/reviews/csv_relabel_thirdparty_${BID}.raw.txt" ]; then
    PAIRS+=("csv_relabel_thirdparty|$BID")
  fi
done
for B in p10_thirdparty/chardet_dom/bugged/P10c_B*.py; do
  BID=$(basename $B .py)
  if [ ! -s "p11_provenance/reviews/chardet_relabel_stdlib_${BID}.raw.txt" ]; then
    PAIRS+=("chardet_relabel_stdlib|$BID")
  fi
done
echo "TOTAL: ${#PAIRS[@]}" >> $LOG

CHUNK=12
i=0
while [ $i -lt ${#PAIRS[@]} ]; do
  PIDS=()
  for ((j=0; j<CHUNK && i+j<${#PAIRS[@]}; j++)); do
    P="${PAIRS[$((i+j))]}"
    TAG="${P%%|*}"; BID="${P#*|}"
    run_one "$BID" "$TAG" &
    PIDS+=($!)
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null
  done
  echo "BATCH i=$i" >> $LOG
  i=$((i + CHUNK))
done
echo "ALL_DONE" >> $LOG
