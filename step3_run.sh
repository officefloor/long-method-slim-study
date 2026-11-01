#!/usr/bin/env bash
#
# Step 3 — scan every usable repository of the sample (docs/ANALYSIS_PLAN.md, section 7).
#
#   ./step3_run.sh
#
# Verifies the sample against its derivation; then the sampler clones each usable repository
# at its pinned commit (shallow, and only the files the scan reads: pins.ONLY), runs the hook (long_method_slim_study.scan: OfficeFloorSlim's
# scan, raw JSON into results/scans/), and deletes the clone. The hook checks that the commit
# scanned is the pinned one. Resumable: a re-run skips what the run log records as done.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
export TMPDIR="$PWD/.tmp"
mkdir -p "$TMPDIR" results/scans

PY=".venv/bin/python"
SAMPLER=".venv/bin/open-source-repository-sampler"
SAMPLE="sample/open-source-repository-sample.csv"
[ -x "$SAMPLER" ] || { echo "ERROR: $SAMPLER not found — run ./step1_setup.sh first"; exit 1; }
[ -f lib/officefloorslim.jar ] || { echo "ERROR: lib/officefloorslim.jar not found — run ./step1_setup.sh first"; exit 1; }
[ -f "$SAMPLE" ] || { echo "ERROR: no sample at $SAMPLE — run ./step2_sample.sh first"; exit 1; }

echo "=== STEP 3: verify the sample ==="
"$SAMPLER" verify "$SAMPLE"

echo
echo "=== STEP 3: scan each usable repository -> results/scans/ ==="
ONLY="$("$PY" -c 'from long_method_slim_study import pins; print(",".join(pins.ONLY))')"
"$SAMPLER" run "$SAMPLE" --only "$ONLY" --run-log results/run-log.jsonl -- \
    "$PY" -m long_method_slim_study.scan --repo {path} --full-name {full_name} --commit {commit} --out results/scans

cat <<'NEXT'

=== STEP 3 complete. ===
Next — the analysis:

    ./step4_analyse.sh

NEXT
