"""Coupling divergence and complexity of the long methods, from the forked measurer (explore.measure),
joined to the scans: the category 4 methods against the other long methods of the same length.

Coupling divergence is the concentration-divergence study's (its PLAN.md and SINEW.md), primary
definition **flow**, all-calls variant: a method with p parameters takes in `1 + p`, and hands on
`sum(1 + a(c))` over its internal calls c (resolved to the code the scan read), `a(c)` the call's
arguments; `d = out - in`. Its roles: **catchment** (d < 0, a leaf that receives data and processes
it), **pipe** (d = 0), **junction** (d > 0).

The same reading for the statement that blocks a category 4 method (the innermost one the instrument
names): the statement taken as a method of its own, its parameters SinewSlim's inputs to it, so it
takes in `1 + inputs` and hands on the internal calls whose line lies inside it (the fork's call
lines). This is an extension of the definition to a statement, not that study's measure.

Complexity: the measurer's cc and cognitive (Campbell) and nesting, over the method's own body
(a lambda belongs to its method, an anonymous class's methods to themselves).

Length is the scan's (code lines). Because cc and cognitive grow with length, every comparison
between groups is made within length bins, and summarised standardised to category 4's length
distribution.
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import statistics
from collections import Counter, defaultdict

from long_method_slim_study.explore.measure import BUDGET, INTERNAL

BINS = [(26, 35), (36, 50), (51, 75), (76, 100), (101, 150), (151, 300), (301, 10 ** 9)]
GROUPS = ("category 4", "category 3", "categories 1-2", "slimmable")


def bin_of(length: int) -> str:
    for lo, hi in BINS:
        if lo <= length <= hi:
            return f"{lo}+" if hi > 10 ** 8 else f"{lo}-{hi}"
    return "under 26"


def group_of(m: dict) -> str | None:
    status = m["sinewslim"]["status"]
    if status in ("slimmable", "slimmable_but_locked"):
        return "slimmable"
    n = (m.get("combined_category") or {}).get("number")
    return {4: "category 4", 3: "category 3", 1: "categories 1-2", 2: "categories 1-2"}.get(n)


def load(directory: str) -> dict[str, dict]:
    """Per repository (OWNER__NAME): an index (path, line) -> [method records], and the document's diagnostics."""
    out = {}
    for path in glob.glob(os.path.join(directory, "*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            doc = json.load(f)
        index = defaultdict(list)
        for fr in doc["files"]:
            for m in fr.get("methods") or []:
                index[(fr["path"], m["decl_line"])].append(m)
                if m["name_line"] != m["decl_line"]:
                    index[(fr["path"], m["name_line"])].append(m)
        out[os.path.basename(path)[:-8]] = {"index": index, "budget_exhausted": doc.get("budget_exhausted"),
                                            "seconds": doc.get("seconds")}
    return out


def join(m: dict, repo: dict | None) -> dict | None:
    """The measurer's record for a scan method: same file, its declaration or name line, the same name."""
    if repo is None:
        return None
    cands = repo["index"].get((m["path"], m["line"]), [])
    name = m["signature"].split("(")[0]
    named = [c for c in cands if c["name"] == name]
    return (named or cands or [None])[0]


def flow(rec: dict, lo: int | None = None, hi: int | None = None, inputs: int | None = None) -> dict:
    """Flow divergence of a method, or of the statement on lines lo..hi with `inputs` parameters."""
    calls = rec["calls"]
    if lo is not None:
        calls = [c for c in calls if len(c) > 4 and lo <= c[4] <= hi]
    out = sum(1 + c[0] for c in calls if c[2] == INTERNAL)
    inn = 1 + (rec["params"] if inputs is None else inputs)
    d = out - inn
    return {"in": inn, "out": out, "d": d, "role": "catchment" if d < 0 else "pipe" if d == 0 else "junction",
            "budget_calls": sum(1 for c in calls if c[2] == BUDGET)}


def summary(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    roles = Counter(r["role"] for r in rows)

    def med(k):
        return statistics.median(r[k] for r in rows)

    return {"n": len(rows), "length": med("length"), "cc": med("cc"), "cognitive": med("cognitive"),
            "nesting": med("nesting"), "cognitive_per_line": round(med("cognitive_per_line"), 3),
            "d": med("d"), "roles": {k: round(roles[k] / len(rows), 4) for k in ("catchment", "pipe", "junction")}}


def standardised(rows_by_bin: dict[str, list[dict]], weights: dict[str, float]) -> dict:
    """Means and role shares within each bin, weighted by category 4's share of methods in that bin."""
    acc, w_used = Counter(), 0.0
    for b, w in weights.items():
        rs = rows_by_bin.get(b) or []
        if not rs:
            continue
        w_used += w
        for k in ("cc", "cognitive", "nesting", "cognitive_per_line"):
            acc[k] += w * statistics.mean(r[k] for r in rs)
        for role in ("catchment", "pipe", "junction"):
            acc[role] += w * sum(1 for r in rs if r["role"] == role) / len(rs)
    if not w_used:
        return {}
    return {"cc": round(acc["cc"] / w_used, 2), "cognitive": round(acc["cognitive"] / w_used, 2),
            "nesting": round(acc["nesting"] / w_used, 2),
            "cognitive_per_line": round(acc["cognitive_per_line"] / w_used, 3),
            "roles": {r: round(acc[r] / w_used, 4) for r in ("catchment", "pipe", "junction")},
            "bins_covered": round(w_used, 4)}


def analyse(scans, measured: dict[str, dict], classes: dict[str, tuple[str, str]],
            statements: dict[str, dict]) -> dict:
    """classes: method key -> (group, class) for category 4; statements: method key -> {lo, hi, inputs}."""
    rows, joined, wanted = defaultdict(list), Counter(), Counter()
    c4rows = []
    for name, _, scan in scans:
        key = name.replace("/", "__")
        repo = measured.get(key)
        if repo is None:
            continue  # not cloned: no category 4 method
        for m in scan["methods"]:
            g = group_of(m)
            if g is None:
                continue
            wanted[g] += 1
            rec = join(m, repo)
            if rec is None:
                continue
            joined[g] += 1
            f = flow(rec)
            row = {"length": m["length"], "cc": rec["cc"], "cognitive": rec["cognitive"], "nesting": rec["nesting"],
                   "cognitive_per_line": rec["cognitive"] / max(1, m["length"]), "d": f["d"], "role": f["role"],
                   "bin": bin_of(m["length"])}
            rows[g].append(row)
            mk = key + "|" + f"{m['path']}:{m['line']}:{m['signature']}"
            if g == "category 4":
                st = statements.get(mk)
                row["statement_role"] = flow(rec, st["lo"], st["hi"], st["inputs"])["role"] if st else None
                row["class"] = classes.get(mk)
                c4rows.append(row)
    bins = [bin_of(lo) for lo, _ in BINS]
    c4bins = Counter(r["bin"] for r in rows["category 4"])
    weights = {b: c4bins[b] / max(1, sum(c4bins.values())) for b in bins}
    by_group = {}
    for g in GROUPS:
        rb = defaultdict(list)
        for r in rows[g]:
            rb[r["bin"]].append(r)
        by_group[g] = {"wanted": wanted[g], "joined": joined[g], **summary(rows[g]),
                       "standardised": standardised(rb, weights),
                       "by_bin": {b: summary(rb[b]) for b in bins if rb[b]}}
    by_class = defaultdict(list)
    for r in c4rows:
        if r["class"]:
            by_class[r["class"]].append(r)
    classes_out = {}
    for (g, c), rs in sorted(by_class.items(), key=lambda t: -len(t[1])):
        st = [r["statement_role"] for r in rs if r["statement_role"]]
        sc = Counter(st)
        classes_out[f"{g} / {c}"] = {**summary(rs), "statement_n": len(st),
                                     "statement_roles": {k: round(sc[k] / len(st), 4) for k in
                                                         ("catchment", "pipe", "junction")} if st else None}
    return {"definition": "flow, all internal calls: in = 1 + parameters, out = sum(1 + arguments); "
                          "d = out - in; catchment d < 0, pipe d = 0, junction d > 0",
            "length_weights": weights, "groups": by_group, "category4_classes": classes_out,
            "repositories_measured": len(measured),
            "budget_exhausted": sorted(k for k, v in measured.items() if v["budget_exhausted"])}
