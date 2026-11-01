#!/usr/bin/env bash
#
# Step 2 — draw the sample (docs/ANALYSIS_PLAN.md, section 3).
#
#   ./step2_sample.sh [any other `open-source-repository-sampler sample` flag]
#
# Draws Java across the sampler's three tiers with the plan's seed, criteria, size and as-of
# date (each repository as it stood before it), the author's own repositories excluded, into
# sample/. The seed is fixed by the plan: this refuses
# --seed, and refuses to draw before the plan is registered (pins.REGISTERED). Commit sample/
# after this step. Interrupted? Re-run the same command to resume the draw.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
# Temporary files (clones) on disk in the project, not in a small RAM-backed /tmp.
export TMPDIR="$PWD/.tmp"
mkdir -p "$TMPDIR"

PY=".venv/bin/python"
SAMPLER=".venv/bin/open-source-repository-sampler"
[ -x "$SAMPLER" ] || { echo "ERROR: $SAMPLER not found — run ./step1_setup.sh first"; exit 1; }
pin() { "$PY" -c "from long_method_slim_study import pins; v = pins.$1; print(','.join(v) if isinstance(v, list) else v)"; }
[ "$(pin REGISTERED)" = "True" ] || { echo "ERROR: the analysis plan is not registered (pins.REGISTERED): no sample is drawn before it is" >&2; exit 1; }
for a in "$@"; do
  case "$a" in --seed|--seed=*) echo "ERROR: the seed is fixed by the plan ($(pin SEED))" >&2; exit 1 ;; esac
done

echo "=== STEP 2: draw Java as of $(pin AS_OF), seed $(pin SEED), target $(pin TARGET) usable -> sample/ ==="
"$SAMPLER" sample --langs "$(pin LANGS)" --tiers "$(pin TIERS)" --target "$(pin TARGET)" --seed "$(pin SEED)" \
    --min-functions "$(pin MIN_FUNCTIONS)" --min-files-with-functions "$(pin MIN_FILES_WITH_FUNCTIONS)" \
    --exclude-owners "$(pin EXCLUDE_OWNERS)" --as-of "$(pin AS_OF)" --out-dir sample "$@"

cat <<'NEXT'

=== STEP 2 complete. ===
Commit sample/ now (its CSV and derivation are the record of what was drawn). Next — run:

    ./step3_run.sh

NEXT
