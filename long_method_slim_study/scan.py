"""The hook the sampler calls for each repository (step 3): OfficeFloorSlim's scan of the clone at
its pinned commit, kept raw as JSON. It computes nothing itself.

    python -m long_method_slim_study.scan --repo PATH --full-name OWNER/NAME --commit SHA --out DIR

The clone is shallow, so the scan reads no growth (`--no-growth`, as the plan measures none). The
JSON must name the pinned commit as the one scanned, or the hook fails and the run log says so.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from long_method_slim_study import pins

JAR = os.path.join("lib", "officefloorslim.jar")


def out_path(out: str, full_name: str) -> str:
    """One file per repository: owner__name.json, so names never collide or nest."""
    return os.path.join(out, full_name.replace("/", "__") + ".json")


def command(repo: str, target: str, java: str = "java", jar: str = JAR) -> list[str]:
    cmd = [java, "-jar", jar, "scan", "--repo", repo, "--no-growth", "--format", "json", "--out", target]
    for g in pins.INCLUDE:
        cmd += ["--include", g]
    for g in pins.EXCLUDE:
        cmd += ["--exclude", g]
    return cmd


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--full-name", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--java", default="java")
    ap.add_argument("--jar", default=JAR)
    a = ap.parse_args(argv)

    os.makedirs(a.out, exist_ok=True)
    target = out_path(a.out, a.full_name)
    done = subprocess.run(command(a.repo, target, a.java, a.jar), capture_output=True, text=True)
    if done.returncode != 0:
        print(f"{a.full_name}: officefloorslim failed ({done.returncode}): {done.stderr.strip()}", file=sys.stderr)
        return 1
    with open(target) as f:
        scanned = json.load(f).get("commit")
    if scanned != a.commit:
        os.remove(target)
        print(f"{a.full_name}: scanned {scanned}, not the pinned {a.commit}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
