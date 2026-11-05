#!/usr/bin/env bash
#
# Step 5 — the write-up (docs/ANALYSIS_PLAN.md, section 7, step 4's "then the write-up").
#
#   ./step5_paper.sh
#
# 1. The post hoc readings (long_method_slim_study/posthoc.py) from the raw scans, the sample and
#    the run log, into results/analysis/posthoc.json: none registered, each labelled so in the paper.
#    With results-0.5.1/scans present (Amendment 3's set-aside scans), they are compared field for
#    field with the scans used; without them the committed comparison is carried forward.
# 2. Every number and table the paper prints (paper/scripts/numbers.py) from analysis.json and
#    posthoc.json, into paper/generated/. No number is typed by hand.
# 3. The paper (paper/build.sh): main.pdf, abstract.txt, arxiv.tar.gz.
# Commit results/analysis/posthoc.json and paper/generated/ with the paper.
set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python"
[ -x "$PY" ] || { echo "ERROR: $PY not found — run ./step1_setup.sh first"; exit 1; }
[ -f results/analysis/analysis.json ] || { echo "ERROR: no results/analysis/analysis.json — run ./step4_analyse.sh first"; exit 1; }

if [ -d results/scans ]; then
  echo "=== STEP 5: the post hoc readings -> results/analysis/posthoc.json ==="
  PREVIOUS=()
  if [ -d results-0.5.1/scans ]; then  # Amendment 3's set-aside scans, compared field for field with the ones used
    PREVIOUS=(--scans-previous results-0.5.1/scans --previous-version 0.5.1)
  fi
  "$PY" -m long_method_slim_study.posthoc --scans results/scans \
      --sample sample/open-source-repository-sample.csv \
      --derivation sample/open-source-repository-sample.derivation.json \
      --run-log results/run-log.jsonl --out results/analysis "${PREVIOUS[@]}"
else
  echo "=== STEP 5: no results/scans; using the committed results/analysis/posthoc.json ==="
  [ -f results/analysis/posthoc.json ] || { echo "ERROR: no results/analysis/posthoc.json either — run ./step3_run.sh first"; exit 1; }
fi

echo
echo "=== STEP 5: the paper's numbers and tables -> paper/generated/ ==="
"$PY" paper/scripts/numbers.py

echo
echo "=== STEP 5: build the paper -> paper/main.pdf ==="
paper/build.sh

cat <<'NEXT'

=== STEP 5 complete. ===
Commit results/analysis/posthoc.json, paper/generated/ and paper/ (main.tex, scripts, build.sh, READMEs).

NEXT
