"""The sampler's hook for the exploratory clones: check the clone is at the pinned commit and record
where it is, so the harness can re-read the source step 3 scanned. The clone is kept (--keep).

    python -m long_method_slim_study.explore.clone_hook --repo PATH --full-name OWNER/NAME --commit SHA \\
        --index exploratory/data/clones.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--full-name", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--index", required=True)
    a = ap.parse_args(argv)
    head = subprocess.run(["git", "-C", a.repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != a.commit:
        print(f"{a.full_name}: clone at {head}, not the pinned {a.commit}", file=sys.stderr)
        return 1
    with open(a.index, "a") as f:
        f.write(json.dumps({"full_name": a.full_name, "commit": a.commit, "path": os.path.abspath(a.repo)}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
