#!/bin/bash
# Auto-extract contracts from each P10 reference module via Codex.
cd "$(dirname "$0")/.."

run_one() {
  local DOMAIN=$1
  local REFFILE=$2
  local OUT="p10_thirdparty/$DOMAIN/contracts/contracts.md"
  if [ -s "$OUT" ]; then echo "skip $DOMAIN"; return 0; fi
  local TMP="/tmp/_p10contract_${DOMAIN}.txt"
  cat > "$TMP" <<EOF
You are a senior Python engineer. Read the following module carefully and produce a self-contained CONTRACT specification document in Markdown.

Format:
# Contracts: ${DOMAIN}

## Module overview
(2-3 sentences: what the module does at a high level)

## Function/method contracts
For each top-level function and class method, document:
- **Signature**
- **Pre-conditions** (what must be true before calling)
- **Post-conditions** (what must be true after returning)
- **Invariants** (properties preserved)
- **Edge cases** (boundary conditions, exceptional inputs)
- **Operator-level invariants** if any (off-by-one, sign, comparison direction)

Be explicit and complete. The contract must be detailed enough that a reviewer who has NEVER seen the module could detect bugs by checking implementation against contracts.

CODE TO ANALYZE:
$(cat p10_thirdparty/$DOMAIN/$REFFILE)
EOF
  codex exec --skip-git-repo-check "$(cat $TMP)" > "$OUT" 2>&1
  echo "DONE $DOMAIN"
}

run_one dateutil_dom ref/relativedelta_module.py &
P1=$!
run_one parsy_dom ref/parsy_module.py &
P2=$!
run_one chardet_dom ref/chardistribution_module.py &
P3=$!
wait $P1 $P2 $P3
echo ALL_CONTRACTS_DONE
