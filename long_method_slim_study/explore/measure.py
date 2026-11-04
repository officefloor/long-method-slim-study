"""Coupling divergence, cyclomatic and cognitive complexity for every method of each clone, by the
concentration-divergence study's measurer, forked to record each call's line.

    python -m long_method_slim_study.explore.measure build            # clone the tag, patch, build, check
    python -m long_method_slim_study.explore.measure run --clones .tmp/explore/clones.jsonl \\
        --out .tmp/explore/measure [--jobs 3]

The measurer is the one tagged analysis-v1 in https://github.com/officefloor/concentration-divergence-study
(its confirmatory measurer: JavaParser 3.28.2 with the symbol solver; per method its parameters,
every call with its argument count and how it resolved, cc, cognitive, nesting, exit points,
tokens, nloc, Halstead volume). The fork (exploratory/measurer-call-lines.patch) appends each
call's first line to the call, so a call can be placed inside a statement; nothing else changes,
and the build is checked against that study's own fixture before any repository is measured.

Each clone is measured over the files the scan read (the study's scope: pins.INCLUDE's Java files,
less pins.EXCLUDE), so a call is internal exactly when it resolves into the code the scan priced.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import fnmatch
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

from long_method_slim_study import pins

REPO = "https://github.com/officefloor/concentration-divergence-study.git"
TAG = "analysis-v1"
COMMIT = "fc7c91d3b67c6ba6f977e36228fc9d8c59f9bf17"
PATCH = os.path.join("exploratory", "measurer-call-lines.patch")
PATCH_SHA256 = "a78b123a3a259f6a9bcf082bc09ba6d40bf743201733b7659e4ba847440b30c8"
JAVAPARSER = "3.28.2"
SOURCE = os.path.join(".tmp", "explore", "divergence-study")
JAR = os.path.join("lib", "divergence-measurer-call-lines.jar")
BUDGET_SECONDS = 3600  # per repository: calls left unresolved after it are marked as budget (resolution 5)
HEAP = os.environ.get("EXPLORE_MEASURER_HEAP", "4g")

# resolutions, as the measurer numbers them
INTERNAL, JDK, NOT_ANALYSED, UNRESOLVED, SHOULD_HAVE, BUDGET = range(6)


def sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def in_scope(path: str) -> bool:
    """The scan's scope for a Java file: pins.INCLUDE's **/*.java, less pins.EXCLUDE's directories."""
    if not path.endswith(".java"):
        return False
    p = "/" + path
    return not any(fnmatch.fnmatch(p, "*/" + g.strip("*/") + "/*") for g in pins.EXCLUDE)


def build() -> dict:
    if sha256(PATCH) != PATCH_SHA256:
        raise SystemExit(f"{PATCH} is not the pinned patch (sha256 {PATCH_SHA256})")
    if os.path.isdir(SOURCE):
        shutil.rmtree(SOURCE)
    subprocess.run(["git", "clone", "-q", REPO, SOURCE], check=True)
    subprocess.run(["git", "-C", SOURCE, "checkout", "-q", TAG], check=True)
    head = subprocess.run(["git", "-C", SOURCE, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != COMMIT:
        raise SystemExit(f"{TAG} is {head}, not the pinned {COMMIT}")
    subprocess.run(["git", "-C", SOURCE, "apply", os.path.abspath(PATCH)], check=True)
    subprocess.run(["mvn", "-q", "-f", os.path.join(SOURCE, "measurer", "pom.xml"), "package"], check=True)
    os.makedirs(os.path.dirname(JAR), exist_ok=True)
    shutil.copy(os.path.join(SOURCE, "measurer", "target", "divergence-measurer.jar"), JAR)
    problems = check()
    if problems:
        raise SystemExit("the measurer failed its check:\n  " + "\n  ".join(problems))
    info = {"repository": REPO, "tag": TAG, "commit": COMMIT, "patch": PATCH, "patch_sha256": PATCH_SHA256,
            "javaparser": JAVAPARSER, "jar_sha256": sha256(JAR),
            "note": "the jar's sha256 differs between builds (Maven timestamps); the tag and the patch fix it"}
    print(json.dumps(info))
    return info


def measure(root: str, files: list[str], out: str, budget: int = BUDGET_SECONDS) -> None:
    with tempfile.TemporaryDirectory() as work:
        lst = os.path.join(work, "files.txt")
        with open(lst, "w", encoding="utf-8") as f:
            f.write("\n".join(files) + "\n")
        part = out + ".part"
        subprocess.run(["java", f"-Xmx{HEAP}", "-Xss16m", "-jar", JAR, "--root", root, "--files", lst, "--out", part,
                        "--budget-seconds", str(budget)], check=True, capture_output=True, text=True,
                       timeout=budget + 3600)
        os.replace(part, out)


# That study's fixture (concentration_divergence_study/javaparser.py) with its expected values, and
# the line of each call the fork adds: (file, method, name line) -> (params, vis, cc, cognitive, nesting, calls)
FIXTURE = {
    "src/main/java/a/T.java": """package a;
public class T {
    public T() { this(1); }
    T(int x) { }
    public int foo(int a, int b) {
        Runnable r = () -> { if (a > 1) { System.out.println(); } };
        Object o = new Object() {
            @Override public String toString() { return a > 0 ? "x" : "y"; }
        };
        return a;
    }
}
""",
    "src/main/java/b/U.java": """package b;
import a.T;
import org.external.Lib;
public class U extends T {
    private int helper(int x) { return x + 1; }
    public int run(String s, int y) {
        int v = helper(y);
        String t = s.trim();
        Lib.call(s, y);
        new T(3);
        if (v > 1 && y > 0) { for (int i = 0; i < y; i++) { if (i % 2 == 0) { v++; } else if (i > 5) { v--; } else { v += 2; } } }
        return run2(v, v, v);
    }
    int run2(int a, int b, int... c) { if (a < 0) { throw new IllegalStateException("x"); } return a; }
    public U() { super(1); }
}
""",
}
EXPECTED = {
    ("src/main/java/a/T.java", "T", 3): (0, "public", 1, 0, 0, [[1, 2, 0, 0, 3]]),
    ("src/main/java/a/T.java", "T", 4): (1, "package", 1, 0, 0, []),
    ("src/main/java/a/T.java", "foo", 5): (2, "public", 2, 2, 2, [[0, 0, 1, -1, 6], [0, 1, 1, -1, 7]]),
    ("src/main/java/a/T.java", "toString", 8): (0, "public", 2, 1, 1, []),
    ("src/main/java/b/U.java", "helper", 5): (1, "private", 1, 0, 0, []),
    ("src/main/java/b/U.java", "run", 6): (2, "public", 6, 9, 3,
                                           [[1, 0, 0, 1, 7], [0, 0, 1, -1, 8], [2, 0, 3, -1, 9],
                                            [1, 1, 0, 0, 10], [3, 0, 0, 1, 12]]),
    ("src/main/java/b/U.java", "run2", 14): (3, "package", 2, 1, 1, [[1, 3, 1, -1, 14]]),
    ("src/main/java/b/U.java", "U", 15): (0, "public", 1, 0, 0, [[1, 2, 0, 0, 15]]),
}


def check() -> list[str]:
    """Problems with the built measurer on that study's fixture; empty when it measures it as expected."""
    with tempfile.TemporaryDirectory() as root:
        for rel, body in FIXTURE.items():
            os.makedirs(os.path.join(root, os.path.dirname(rel)), exist_ok=True)
            with open(os.path.join(root, rel), "w") as f:
                f.write(body)
        out = os.path.join(root, "out.json.gz")
        try:
            measure(root, sorted(FIXTURE), out, budget=600)
        except subprocess.CalledProcessError as e:
            return [f"exited {e.returncode}: {e.stderr[-500:]}"]
        with gzip.open(out, "rt") as f:
            doc = json.load(f)
    problems = []
    if doc.get("javaparser") != JAVAPARSER:
        problems.append(f"JavaParser {doc.get('javaparser')!r}, not {JAVAPARSER}")
    got = {(fr["path"], m["name"], m["name_line"]): (m["params"], m["vis"], m["cc"], m["cognitive"], m["nesting"],
                                                      m["calls"])
           for fr in doc["files"] for m in fr.get("methods") or []}
    for k, v in EXPECTED.items():
        if got.get(k) != v:
            problems.append(f"{k}: expected {v}, got {got.get(k)}")
    return problems


def files_of(clone: str) -> list[str]:
    out = []
    for d, _, names in os.walk(clone):
        if "/.git" in d:
            continue
        for n in names:
            rel = os.path.relpath(os.path.join(d, n), clone).replace(os.sep, "/")
            if in_scope(rel):
                out.append(rel)
    return sorted(out)


def run(clones: str, out_dir: str, jobs: int) -> int:
    if not os.path.isfile(JAR):
        raise SystemExit(f"no {JAR}: run the build first")
    os.makedirs(out_dir, exist_ok=True)
    with open(clones) as f:
        todo = [json.loads(line) for line in f]
    todo = [c for c in todo if not os.path.exists(os.path.join(out_dir, c["full_name"].replace("/", "__") + ".json.gz"))]

    def one(c: dict) -> str:
        out = os.path.join(out_dir, c["full_name"].replace("/", "__") + ".json.gz")
        files = files_of(c["path"])
        try:
            measure(c["path"], files, out)
            return f"{len(files)} files"
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            return f"failed: {str(getattr(e, 'stderr', e))[-300:]}"

    with concurrent.futures.ThreadPoolExecutor(jobs) as pool:
        futures = {pool.submit(one, c): c["full_name"] for c in todo}
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            print(f"[{i}/{len(todo)}] {futures[fut]}: {fut.result()}", flush=True)
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    r = sub.add_parser("run")
    r.add_argument("--clones", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        build()
        return 0
    return run(a.clones, a.out, a.jobs)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
