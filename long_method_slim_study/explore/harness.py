"""Run the exploratory harness (exploratory/harness/Explore.java) over every cloned repository's
category 4 methods.

    python -m long_method_slim_study.explore.harness --scans results/scans \\
        --clones .tmp/explore/clones.jsonl --out .tmp/explore/harness [--jobs 6]

Per repository, the targets (each category 4 method, with the lines of the statement that blocks the
combined split and of the innermost statement SinewSlim names) are dealt into chunks of at most
--chunk methods; each chunk is one JVM, --jobs at a time, appending one JSON line per method to
OWNER__NAME#i.jsonl. A JVM that runs past the timeout is killed and restarted; the method it was on
is recorded as a timeout and skipped, so a run always ends. A re-run resumes: what has a result (of the version the target asks for) or a
timeout is skipped, and a method an interrupted run only started is tried again.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys

from long_method_slim_study import scan as scan_hook
from long_method_slim_study.explore import rootcause

JAR = os.path.join("lib", "officefloorslim.jar")
CLASSES = os.path.join("exploratory", "harness", "classes")
SOURCE = os.path.join("exploratory", "harness", "Explore.java")
LINES = re.compile(r"at lines (\d+)-(\d+)")
# the result version each target needs (Explore.VERSION): versions 2 and 3 added the jumps and body shape that
# the control methods' classes rest on, so a control method read at version 1 is read again
CONTROL_VERSION = 3


def blocking_lines(detail: str | None) -> tuple[dict | None, dict | None]:
    """The outer blocking statement (the combined split's) and the innermost one SinewSlim names, as line ranges."""
    if not detail:
        return None, None
    found = LINES.findall(detail)
    outer = {"start": int(found[0][0]), "end": int(found[0][1])} if found else None
    inner = None
    if "as a function body" in detail and len(found) > 1:
        inner = {"start": int(found[-1][0]), "end": int(found[-1][1])}
    return outer, inner


def targets(scan: dict) -> list[dict]:
    out = []
    for m in scan["methods"]:
        if (m.get("combined_category") or {}).get("number") != 4:
            continue
        outer, inner = blocking_lines(m["combined"].get("detail"))
        group, _ = rootcause.root(m["combined"])
        out.append({"path": m["path"], "line": m["line"], "signature": m["signature"], "outer": outer, "inner": inner,
                    "version": CONTROL_VERSION if group == "control" else 1})
    return out


def compile_harness() -> None:
    os.makedirs(CLASSES, exist_ok=True)
    subprocess.run(["javac", "--release", "17", "-nowarn", "-cp", JAR, "-d", CLASSES, SOURCE], check=True,
                   capture_output=True)


def record_timeout(out_file: str) -> None:
    """After a JVM is killed for its time: the last method it started, with no result, is a timeout."""
    if not os.path.exists(out_file):
        return
    started, finished = [], set()
    with open(out_file) as f:
        for line in f:
            r = json.loads(line)
            (started.append(r["id"]) if r.get("start") else finished.add(r["id"]))
    open_ids = [i for i in started if i not in finished]
    if open_ids:
        with open(out_file, "a") as f:
            f.write(json.dumps({"id": open_ids[-1], "timeout": True}) + "\n")


def run_chunk(clone: str, target_file: str, out_file: str, n: int, timeout: int) -> str:
    for _ in range(n + 1):  # at most one restart per method
        try:
            subprocess.run(["java", "-Xss16m", "-Xmx2g", "-cp", f"{JAR}{os.pathsep}{CLASSES}", "Explore", clone,
                            target_file, out_file], check=True, timeout=timeout, capture_output=True, text=True)
            return "done"
        except subprocess.TimeoutExpired:
            record_timeout(out_file)  # the method it was on is recorded, and skipped on the restart
            continue
        except subprocess.CalledProcessError as e:
            return f"failed: {e.stderr.strip()[-400:]}"
    return "gave up"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scans", required=True)
    ap.add_argument("--clones", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=600, help="seconds per JVM run before it is restarted")
    ap.add_argument("--jobs", type=int, default=6, help="JVMs at once (each up to 2 GB of heap)")
    ap.add_argument("--chunk", type=int, default=100, help="methods per JVM")
    a = ap.parse_args(argv)
    compile_harness()
    os.makedirs(a.out, exist_ok=True)
    with open(a.clones) as f:
        clones = [json.loads(line) for line in f]
    jobs = []
    for c in clones:
        name = c["full_name"]
        with open(scan_hook.out_path(a.scans, name)) as f:
            scan = json.load(f)
        if scan.get("commit") != c["commit"]:
            print(f"{name}: the clone's commit is not the scan's", file=sys.stderr)
            return 1
        t = targets(scan)
        base = os.path.join(a.out, name.replace("/", "__"))
        for i in range(0, len(t), a.chunk):
            part = f"{base}#{i // a.chunk}"
            with open(part + ".targets.json", "w") as f:
                json.dump(t[i:i + a.chunk], f)
            jobs.append((name, c["path"], part, len(t[i:i + a.chunk])))
    jobs.sort(key=lambda j: -j[3])  # the largest chunks first
    with concurrent.futures.ThreadPoolExecutor(a.jobs) as pool:
        futures = {pool.submit(run_chunk, path, part + ".targets.json", part + ".jsonl", n, a.timeout): (name, part, n)
                   for name, path, part, n in jobs}
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            name, part, n = futures[fut]
            print(f"[{i}/{len(jobs)}] {os.path.basename(part)}: {n} methods, {fut.result()}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
