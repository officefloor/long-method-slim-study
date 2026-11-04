"""Fetch each usable repository's GitHub description and topics, once, into a dated snapshot, so the
domain coding (explore.domains) reads a fixed file rather than a live API whose answers change.

    python -m long_method_slim_study.explore.meta --sample sample/open-source-repository-sample.csv \\
        --out exploratory/data/repo-meta.json

Needs the GitHub CLI (`gh`), authenticated. A repository that is gone or renamed is recorded with
its error; it is coded from its name alone.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import subprocess
import sys


def fetch(full_name: str) -> dict:
    done = subprocess.run(["gh", "api", f"repos/{full_name}", "--jq",
                           "{description, topics, homepage, archived, full_name}"],
                          capture_output=True, text=True)
    if done.returncode != 0:
        return {"error": done.stderr.strip()[:200]}
    return json.loads(done.stdout)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    with open(a.sample, newline="") as f:
        names = [r["full_name"] for r in csv.DictReader(f) if r["status"] == "usable"]
    repos = {}
    for i, n in enumerate(names, 1):
        repos[n] = fetch(n)
        if i % 50 == 0:
            print(f"{i}/{len(names)}", flush=True)
    with open(a.out, "w") as f:
        json.dump({"fetched_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                   "source": "GitHub REST API, repos/{owner}/{name}: description, topics, homepage, archived",
                   "repositories": repos}, f, indent=1, sort_keys=True)
    print(f"{len(repos)} repositories, {sum(1 for r in repos.values() if 'error' in r)} errors -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
