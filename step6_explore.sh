#!/usr/bin/env bash
#
# Step 6 — exploratory (not registered; changes no registered figure, hypothesis or reading): re-read
# the category 4 methods, to propose the next hypotheses. See exploratory/README.md.
#
#   ./step6_explore.sh [--refresh-meta]
#
# Needs steps 1 and 3 done (the venv, lib/officefloorslim.jar, results/scans/), a JDK (javac 17+),
# Maven, and the network for the clones and the measurer's source.
#
#   1. select   the repositories whose scan holds a category 4 method -> .tmp/explore/category4-sample.csv
#   2. clone    each at its pinned commit, .java only, kept, SHARDS samplers in parallel; resumable
#   3. meta     the GitHub description and topics snapshot, exploratory/data/repo-meta.json: fetched
#               only when missing or with --refresh-meta (the committed snapshot is what was coded)
#   4. harness  exploratory/harness/Explore.java over every category 4 method -> .tmp/explore/harness/
#   5. measure  the concentration-divergence study's measurer (tag analysis-v1, plus
#               exploratory/measurer-call-lines.patch: each call's line), built and checked on that
#               study's fixture, over every clone: coupling divergence, cc, cognitive -> .tmp/explore/measure/
#   6. report   exploratory/results/explore.json and exploratory/results/tables.md
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
export TMPDIR="$PWD/.tmp"
PY=".venv/bin/python"
SAMPLER=".venv/bin/open-source-repository-sampler"
WORK=".tmp/explore"
SHARDS="${SHARDS:-4}"
SAMPLE="sample/open-source-repository-sample.csv"
DERIVATION="sample/open-source-repository-sample.derivation.json"
[ -d results/scans ] || { echo "ERROR: no results/scans — run ./step3_run.sh first"; exit 1; }
[ -f lib/officefloorslim.jar ] || { echo "ERROR: lib/officefloorslim.jar not found — run ./step1_setup.sh first"; exit 1; }
mkdir -p "$WORK/clones"

echo "=== EXPLORE 1: select the repositories with a category 4 method ==="
"$PY" -m long_method_slim_study.explore.select --scans results/scans --sample "$SAMPLE" \
    --out "$WORK/category4-sample.csv" --shards "$SHARDS"

echo "=== EXPLORE 2: clone them at their pinned commits ($SHARDS in parallel) ==="
echo "progress: tail -f $WORK/clone.*.out (a repository already in the run logs is skipped)"
pids=()
for i in $(seq 0 $((SHARDS - 1))); do
  "$SAMPLER" run "$WORK/category4-sample.$i.csv" --only .java --keep --work-dir "$WORK/clones" \
      --run-log "$WORK/clone-log.$i.jsonl" -- \
      "$PY" -m long_method_slim_study.explore.clone_hook --repo {path} --full-name {full_name} \
      --commit {commit} --index "$WORK/clones.jsonl" > "$WORK/clone.$i.out" 2>&1 &
  pids+=($!)
done
for p in "${pids[@]}"; do wait "$p"; done
echo "$(wc -l < "$WORK/clones.jsonl") repositories cloned"

echo "=== EXPLORE 3: the repositories' descriptions and topics ==="
if [ ! -f exploratory/data/repo-meta.json ] || [ "${1:-}" = "--refresh-meta" ]; then
  "$PY" -m long_method_slim_study.explore.meta --sample "$SAMPLE" --out exploratory/data/repo-meta.json
else
  echo "using the committed snapshot exploratory/data/repo-meta.json"
fi

echo "=== EXPLORE 4: the harness over every category 4 method ==="
"$PY" -m long_method_slim_study.explore.harness --scans results/scans --clones "$WORK/clones.jsonl" \
    --out "$WORK/harness"

echo "=== EXPLORE 5: coupling divergence and complexity, by the forked measurer ==="
[ -f lib/divergence-measurer-call-lines.jar ] && "$PY" -c \
    'import sys; from long_method_slim_study.explore import measure; sys.exit(1 if measure.check() else 0)' \
    || "$PY" -m long_method_slim_study.explore.measure build
"$PY" -m long_method_slim_study.explore.measure run --clones "$WORK/clones.jsonl" --out "$WORK/measure"

echo "=== EXPLORE 6: the report ==="
"$PY" -m long_method_slim_study.explore.report --scans results/scans --sample "$SAMPLE" \
    --derivation "$DERIVATION" --harness "$WORK/harness" --measure "$WORK/measure" \
    --meta exploratory/data/repo-meta.json \
    --out exploratory/results/explore.json --tables exploratory/results/tables.md

echo "Done. Commit exploratory/results/ (and exploratory/data/repo-meta.json if refreshed)."
