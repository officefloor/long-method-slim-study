#!/usr/bin/env bash
#
# Step 4 — the analysis (docs/ANALYSIS_PLAN.md, sections 5 and 6).
#
#   ./step4_analyse.sh
#
# Reads the raw scans, the sample and its derivation, and writes results/analysis/analysis.json:
# every measure per repository, per tier and pooled; the headline ratios with stratified
# bootstrap intervals and population weights; every method where the split's worst seam is
# larger than SinewSlim's; and the usable repositories not scanned. It counts what the scans
# report and computes no cost of its own.
set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python"
[ -x "$PY" ] || { echo "ERROR: $PY not found — run ./step1_setup.sh first"; exit 1; }
[ -d results/scans ] || { echo "ERROR: no results/scans — run ./step3_run.sh first"; exit 1; }

echo "=== STEP 4: analyse -> results/analysis/ ==="
"$PY" -m long_method_slim_study.analyse --scans results/scans \
    --sample sample/open-source-repository-sample.csv \
    --derivation sample/open-source-repository-sample.derivation.json \
    --out results/analysis

cat <<'NEXT'

=== STEP 4 complete. ===
The figures are in results/analysis/analysis.json; commit results/ with them (the raw scans are
the evidence for every figure).

NEXT
