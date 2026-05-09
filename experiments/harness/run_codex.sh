#!/bin/bash
# Usage: run_codex.sh <task> <cond> <run_id>
# Reads prompts/${cond}_${task}.txt, writes runs/codex_${task}_${cond}_${run_id}.py
set -e
TASK=$1
COND=$2
RUN=$3
PROMPT_FILE="prompts/${COND}_${TASK}.txt"
OUT_RAW="runs/codex_${TASK}_${COND}_${RUN}.raw.txt"
OUT_PY="runs/codex_${TASK}_${COND}_${RUN}.py"

mkdir -p runs
codex exec --skip-git-repo-check "$(cat $PROMPT_FILE)" > "$OUT_RAW" 2>&1
python harness/extract_code.py "$OUT_RAW" > "$OUT_PY"
wc -c "$OUT_RAW" "$OUT_PY"
