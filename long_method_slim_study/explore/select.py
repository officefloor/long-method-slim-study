"""Select the repositories the exploratory re-read needs: those whose scan holds at least one
category 4 method under the combined split (stuck, and no plan from either side).

    python -m long_method_slim_study.explore.select --scans results/scans \\
        --sample sample/open-source-repository-sample.csv --out exploratory/data/category4-sample.csv

Writes the sample's own rows (same columns, same pinned commits), so the sampler clones exactly what
step 3 scanned; with --shards N, also the same rows dealt into N files, to clone in parallel.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys


def category4_count(scan: dict) -> int:
    return sum(1 for m in scan["methods"] if (m.get("combined_category") or {}).get("number") == 4)


def scan_path(scans: str, full_name: str) -> str:
    return os.path.join(scans, full_name.replace("/", "__") + ".json")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scans", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shards", type=int, default=0,
                    help="also write OUT's rows dealt into this many CSVs (OUT.0.csv ...), to clone in parallel")
    a = ap.parse_args(argv)
    with open(a.sample, newline="") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    keep = []
    for r in rows:
        if r["status"] != "usable":
            continue
        p = scan_path(a.scans, r["full_name"])
        if os.path.exists(p):
            with open(p) as f:
                if category4_count(json.load(f)):
                    keep.append(r)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(keep)
    for i in range(a.shards):
        with open(f"{a.out[:-4]}.{i}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(keep[i::a.shards])
    print(f"{len(keep)} repositories with a category 4 method -> {a.out}" + (f" ({a.shards} shards)" if a.shards else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
