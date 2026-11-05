#!/usr/bin/env bash
#
# Price the paper's two worked examples (Examples.java) with the pinned OfficeFloorSlim release, into
# scan.json, which paper/scripts/numbers.py reads for every cost the paper prints about them; and list
# SinewSlim's pieces (the scan reports their cost, width and count, not the pieces themselves) into
# sinewslim-pieces.json by ../scripts/SinewSlimPieces.java, against the SinewSlim classes the same jar
# bundles (kept out of this directory so that the scan does not read it).
#
#   paper/examples/scan.sh        # from the repository root, after ./step1_setup.sh
set -euo pipefail
cd "$(dirname "$0")"
JAR=../../lib/officefloorslim.jar
java -jar "$JAR" scan --repo . --no-growth --format json --out scan.json
python3 - <<'PY'
import json
s = json.load(open("scan.json"))
s["repository"] = "paper/examples"  # not the absolute path of whoever ran it
json.dump(s, open("scan.json", "w"), indent=2)
for m in s["methods"]:
    print(m["signature"], m["length"], "lines:", m["sinewslim"]["status"], m["sinewslim"].get("cost"),
          "| injection", m["officefloor"]["total"], "| combined", m["combined"]["sum"])
PY
BUILD="$(mktemp -d)"
javac --release 17 -cp "$JAR" -d "$BUILD" ../scripts/SinewSlimPieces.java
java -cp "$JAR:$BUILD" SinewSlimPieces src/main/java/example/Examples.java "$(java -jar "$JAR" --version)" sinewslim-pieces.json
rm -rf "$BUILD"
cat sinewslim-pieces.json
