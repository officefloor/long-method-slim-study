#!/usr/bin/env bash
#
# Step 1 — set up for replication (docs/ANALYSIS_PLAN.md, section 7).
#
#   ./step1_setup.sh
#
# A thin alias for ./setup.sh: .venv with the pinned open-source-repository-sampler and this
# package; the released OfficeFloorSlim command line into ./lib, sha256-verified against
# long_method_slim_study/pins.py; then the tests.
set -euo pipefail
cd "$(dirname "$0")"

echo "=== STEP 1: setup ==="
./setup.sh "$@"

cat <<'NEXT'

=== STEP 1 complete. ===
Next — draw the sample, once the analysis plan is registered:

    ./step2_sample.sh

NEXT
