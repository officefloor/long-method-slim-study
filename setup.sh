#!/usr/bin/env bash
#
# Set up for replication: .venv with the pinned sampler and this package; the released
# OfficeFloorSlim command line into ./lib, its sha256 checked against the pin; then the tests.
#
# Needs on the machine: python3, git, Java 17+, and curl. Step 2 (sampling) also needs the GitHub
# CLI authenticated (`gh auth login`).
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e .
echo "sampler: $(.venv/bin/open-source-repository-sampler --version 2>&1 | head -1)"

PY=".venv/bin/python"
missing="$("$PY" -c 'from long_method_slim_study import pins; print(" ".join(pins.unsettled()))')"
if [ -n "$missing" ]; then
  echo "ERROR: not pinned yet in long_method_slim_study/pins.py: $missing" >&2
  echo "       (the released OfficeFloorSlim the study calls; docs/ANALYSIS_PLAN.md, section 4)" >&2
  exit 1
fi
VERSION="$("$PY" -c 'from long_method_slim_study import pins; print(pins.OFFICEFLOORSLIM_VERSION)')"
SHA="$("$PY" -c 'from long_method_slim_study import pins; print(pins.OFFICEFLOORSLIM_JAR_SHA256)')"
mkdir -p lib
JAR="lib/officefloorslim.jar"
if [ ! -f "$JAR" ] || ! echo "$SHA  $JAR" | sha256sum --check --quiet - 2>/dev/null; then
  curl --fail --location --silent --show-error -o "$JAR" \
    "https://github.com/officefloor/OfficeFloorSlim/releases/download/v$VERSION/officefloorslim.jar"
fi
echo "$SHA  $JAR" | sha256sum --check - || { rm -f "$JAR"; echo "ERROR: $JAR is not the pinned release" >&2; exit 1; }
java -jar "$JAR" --version

"$PY" -m unittest discover -s tests -t .
