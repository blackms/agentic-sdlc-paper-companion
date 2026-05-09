#!/bin/bash
# Usage: run_gemini.sh <task> <cond> <run_id>
TASK=$1
COND=$2
RUN=$3
PROMPT_FILE="prompts/${COND}_${TASK}.txt"
OUT_RAW="runs/gemini_${TASK}_${COND}_${RUN}.raw.txt"
OUT_PY="runs/gemini_${TASK}_${COND}_${RUN}.py"

mkdir -p runs
gemini --model gemini-2.5-flash -p "$(cat $PROMPT_FILE)" > "$OUT_RAW" 2>&1
python harness/extract_code.py "$OUT_RAW" > "$OUT_PY"
wc -c "$OUT_PY"
