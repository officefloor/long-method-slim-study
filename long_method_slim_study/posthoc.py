"""Post hoc readings for the write-up (none registered in docs/ANALYSIS_PLAN.md): computed from the
raw scans after the registered analysis (step 4) was read, and labelled so wherever the paper
prints them. Like the analysis, it counts what OfficeFloorSlim reported and computes no cost.

    python -m long_method_slim_study.posthoc --scans results/scans --sample sample/X.csv \\
        --derivation sample/X.derivation.json --run-log results/run-log.jsonl --out results/analysis

What it writes (results/analysis/posthoc.json):

- test_paths: the registered scope left out `**/test/**` and `**/tests/**`, which misses test code
  in directories named otherwise (`guava-tests`, `internalClusterTest`, `androidTest`). The
  headline figures recomputed with every method under a directory whose name contains "test"
  left out: a sensitivity reading, not the registered one.
- construction_exceptions: long methods SinewSlim slims for which the combined split has no plan,
  which the plan's section 5 says cannot happen by construction.
- improved_strict_over_slimmable: H2 read against plain extraction: the combined split's sum
  strictly below SinewSlim's cost itself (a saving of 2 or more), not below its cost plus 1.
- category3c_per_repository: the quartiles of each repository's own H1 share, and how many
  repositories with a stuck method have no rescued method at all.
- category4_machine_written: a lower bound on machine-written code among the category 4 methods.
- sequence_population: the long methods a straight sequence of functions is the way to split (the
  combined split's plan has no decision and is improved or rescued), over the long methods, with the
  strict reading (a saving of 2 or more) and the ties beside it.
- the composition of the rescued and improved methods (functions alone, or extracted methods
  inside them), the savings, the worse-seam differences, how the stuck methods concentrate in a
  few repositories, the per-tier per-repository medians, the readings, the unparsed files and the
  scan times.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import statistics
import sys
from collections import Counter

from long_method_slim_study import analyse, pins

TEST_RULE = "a method whose path has a directory segment containing 'test' (case-insensitive) is left out"
# Machine-written code among the category 4 methods (post hoc, a lower bound): the methods GUI builders
# name (NetBeans, JBuilder, IntelliJ's designer), and methods of 500 code lines or more (generated tables).
GUI_BUILDER_METHODS = ("initComponents", "jbInit", "$$$setupUI$$$")
LONG_TABLE_LINES = 500
MACHINE_RULE = (f"a category 4 method (combined split) named {', '.join(GUI_BUILDER_METHODS)}, "
                f"or of {LONG_TABLE_LINES} code lines or more")


def is_test_path(path: str) -> bool:
    return any("test" in seg.lower() for seg in path.split("/")[:-1])


def load_rows(scans_dir: str, sample_csv: str):
    with open(sample_csv, newline="") as f:
        sample = list(csv.DictReader(f))
    usable = {r["full_name"]: r for r in sample if r["status"] == "usable"}
    scans = []
    for name, r in usable.items():
        path = os.path.join(scans_dir, name.replace("/", "__") + ".json")
        if os.path.exists(path):
            with open(path) as f:
                scans.append((name, r["tier"], json.load(f)))
    return scans


def test_path_sensitivity(scans, weights) -> dict:
    rows, dropped, segments, repos = [], Counter(), Counter(), set()
    for name, tier, scan in scans:
        kept = []
        for m in scan["methods"]:
            if is_test_path(m["path"]):
                dropped["long"] += 1
                repos.add(name)
                segments[next(s for s in m["path"].split("/")[:-1] if "test" in s.lower())] += 1
                if m["sinewslim"]["status"] in analyse.STUCK:
                    dropped["stuck"] += 1
                    if m["combined_category"]["number"] == 3:
                        dropped["category3c"] += 1
                    if m["category"]["number"] == 3:
                        dropped["category3"] += 1
                elif m["sinewslim"].get("cost") is not None:
                    dropped["slimmable"] += 1
                    c = m["combined"]
                    if c["feasible"] and not c["extraction_only"] and m["sinewslim"]["cost"] + 1 - c["sum"] > 0:
                        dropped["improved"] += 1
            else:
                kept.append(m)
        s = dict(scan, methods=kept, long_methods=len(kept))
        rows.append({"full_name": name, "tier": tier, **analyse.repository(s)})
    return {"rule": TEST_RULE, "repositories_affected": len(repos), "dropped": dict(dropped),
            "segments": segments.most_common(12), "headline": analyse.headline(rows, weights)}


def per_tier_medians(rows, num, den) -> dict:
    return {t: analyse.per_repository([r for r in rows if r["tier"] == t], num, den)
            for t in sorted({r["tier"] for r in rows})}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scans", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--derivation", required=True)
    ap.add_argument("--run-log", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    with open(a.derivation) as f:
        weights = analyse.weights_from(json.load(f))
    scans = load_rows(a.scans, a.sample)

    exceptions, c3_pieces, improved_pieces, savings, seam_diff = [], Counter(), Counter(), [], Counter()
    readings_long, of_repos, of_evidence, unparsed, longest, per = Counter(), Counter(), Counter(), Counter(), [], []
    stuck_without_plan_combined, gain_by_reason = Counter(), Counter()
    by_category, planned_by_category, lost, machine = Counter(), Counter(), [], Counter()
    shapes = {"rescued": Counter(), "improved": Counter(), "tied": Counter()}
    seq_by_repo = {}  # per repository: the long methods whose chosen plan is a sequence, by group
    for name, tier, scan in scans:
        seq = seq_by_repo[name] = Counter()
        unparsed[name] += len(scan["unparsed"])
        stuck = c3 = 0
        for m in scan["methods"]:
            s, o, c = m["sinewslim"], m["officefloor"], m["combined"]
            readings_long[m["reading"]] += 1
            if m["reading"] == "officefloor_function":
                of_repos[name] += 1
                of_evidence[m["evidence"].split(" ")[0]] += 1
            longest.append((m["length"], name, f"{m['type']}.{m['signature']}"))
            is_stuck = s["status"] in analyse.STUCK
            if is_stuck:
                stuck += 1
                k = m["category"]["number"]
                by_category[k] += 1
                if c["feasible"]:
                    planned_by_category[k] += 1
                elif k == 3:
                    lost.append({"repository": name, "path": m["path"], "method": f"{m['type']}.{m['signature']}",
                                 "line": m["line"], "combined_reason": c["reason"], "combined_detail": c.get("detail")})
                if not c["feasible"]:
                    stuck_without_plan_combined[c["reason"]] += 1
                if m["combined_category"]["number"] == 3:
                    c3 += 1
                    c3_pieces[c["pieces"]] += 1
                    if m["category"]["number"] != 3:
                        gain_by_reason[o["reason"]] += 1
                if m["combined_category"]["number"] == 4:
                    gui = m["signature"].split("(")[0] in GUI_BUILDER_METHODS
                    big = m["length"] >= LONG_TABLE_LINES
                    machine["category4"] += 1
                    machine["gui_builder"] += gui
                    machine["long_table"] += big
                    machine["either"] += gui or big
            elif s.get("cost") is not None:
                if not c["feasible"]:
                    exceptions.append({"repository": name, "path": m["path"], "method": f"{m['type']}.{m['signature']}",
                                       "line": m["line"], "length": m["length"], "sinewslim_status": s["status"],
                                       "sinewslim_cost": s["cost"], "combined_reason": c["reason"],
                                       "combined_detail": c.get("detail")})
                elif not c["extraction_only"]:
                    saving = s["cost"] + 1 - c["sum"]
                    if saving > 0:
                        savings.append(saving)
                        improved_pieces["with_pieces" if c["pieces"] else "functions_only"] += 1
            if c["feasible"] and not c["extraction_only"]:
                # the plan's shape, from its functions and links: a straight sequence of functions, or
                # branching (a decision whose branches are flows), each with or without early returns (a
                # return link from a function other than the last: the last function's return is the end)
                shape = ("branching" if any(fn["kind"] == "decision" for fn in c["functions"]) else "sequence") \
                    + (" with early returns" if any(l["kind"] == "return" and l["from"] != len(c["functions"]) - 1
                                                    for l in c["links"]) else "")
                is_sequence = shape.startswith("sequence")
                if is_stuck:
                    if m["combined_category"]["number"] == 3:
                        shapes["rescued"][shape] += 1
                        seq["injection_rescued"] += 1
                        seq["sequence_rescued"] += is_sequence
                elif s.get("cost") is not None:
                    saving = s["cost"] + 1 - c["sum"]
                    if saving > 0:
                        shapes["improved"][shape] += 1
                        seq["injection_improved"] += 1
                        seq["sequence_improved"] += is_sequence
                        seq["sequence_improved_strict"] += is_sequence and saving >= 2
                    elif saving == 0:
                        shapes["tied"][shape] += 1
                        seq["sequence_tied"] += is_sequence
            if s.get("cost") is not None and o["feasible"] and o["worst_seam"] > s["width"]:
                seam_diff[o["worst_seam"] - s["width"]] += 1
        per.append({"repository": name, "tier": tier, "long": len(scan["methods"]), "stuck": stuck, "category3c": c3,
                    "methods": sum(scan["methods_by_reading"].values())})
    longest.sort(reverse=True)
    per.sort(key=lambda p: -p["stuck"])
    s1 = sum(p["stuck"] for p in per)

    rows = [{"full_name": n, "tier": t, **analyse.repository(sc)} for n, t, sc in scans]
    for r in rows:  # the stuck methods nothing conventional fixes: categories 3 and 4 under the injection split
        r["stuck_not_conventional"] = r["category"].get("3", 0) + r["category"].get("4", 0)
        # improved by 2 or more: the sum strictly below SinewSlim's cost itself, not its cost plus 1
        r["improved_strict"] = sum(v for k, v in r["savings"].items() if int(k) >= 2)
        # the long methods a straight sequence of functions is the way to split: the plan is a sequence and
        # either cheaper than extraction (improved) or the only plan (rescued, category 3 combined)
        q = seq_by_repo[r["full_name"]]
        r["sequence_way"] = q["sequence_improved"] + q["sequence_rescued"]
        r["sequence_way_strict"] = q["sequence_improved_strict"] + q["sequence_rescued"]
        r["sequence_way_with_tied"] = r["sequence_way"] + q["sequence_tied"]
        r["injection_way"] = q["injection_improved"] + q["injection_rescued"]
        r["sequence_improved"], r["sequence_rescued"] = q["sequence_improved"], q["sequence_rescued"]
    c3_shares = sorted(r["combined_category"].get("3", 0) / r["stuck"] for r in rows if r["stuck"])
    with open(a.run_log) as f:
        log = [json.loads(line) for line in f]
    secs = sorted(((r["seconds"], r["full_name"]) for r in log if r.get("seconds") is not None), reverse=True)
    finished = sorted(r["finished_utc"] for r in log if r.get("finished_utc"))

    out = {
        "schema": "long-method-slim-study-posthoc/1",
        "status": "post hoc: none of this was registered; computed after the registered analysis was read",
        "test_paths": test_path_sensitivity(scans, weights),
        "construction_exceptions": exceptions,
        "category3c_composition": {"functions_only": c3_pieces.get(0, 0),
                                   "with_pieces": sum(v for k, v in c3_pieces.items() if k > 0),
                                   "pieces_histogram": {str(k): v for k, v in sorted(c3_pieces.items())}},
        "plan_shapes": {k: dict(sorted(v.items())) for k, v in shapes.items()},
        "sequence_population": {
            "rule": "a long method whose combined-split plan has no decision function, and is improved "
                    "(sum below SinewSlim's cost plus 1) or rescued (category 3, combined split); "
                    "strict: improved by 2 or more (below SinewSlim's cost itself)",
            "sequence_way_over_long": analyse.figure(rows, weights, "sequence_way", "long"),
            "sequence_way_strict_over_long": analyse.figure(rows, weights, "sequence_way_strict", "long"),
            "sequence_way_with_tied_over_long": analyse.figure(rows, weights, "sequence_way_with_tied", "long"),
            "injection_way_over_long": analyse.figure(rows, weights, "injection_way", "long"),
            "sequence_improved_over_long": analyse.figure(rows, weights, "sequence_improved", "long"),
            "sequence_rescued_over_long": analyse.figure(rows, weights, "sequence_rescued", "long"),
            "sequence_way_over_methods": analyse.figure(rows, weights, "sequence_way", "methods")},
        "plans_by_category": {str(k): {"stuck": by_category[k], "combined_has_plan": planned_by_category[k],
                                       "share": round(planned_by_category[k] / by_category[k], 4) if by_category[k] else None}
                              for k in sorted(by_category)},
        "category3c_over_not_conventional": analyse.figure(rows, weights, "combined_category.3", "stuck_not_conventional"),
        "category3c_per_repository": {"repositories": len(c3_shares),
                                      "quartiles": [round(q, 4) for q in statistics.quantiles(c3_shares, n=4)],
                                      "without_category3c": sum(1 for x in c3_shares if x == 0)},
        "improved_strict_over_slimmable": analyse.figure(rows, weights, "improved_strict", "slimmable"),
        "category4_machine_written": {"rule": MACHINE_RULE, "gui_builder_methods": list(GUI_BUILDER_METHODS),
                                      "long_table_lines": LONG_TABLE_LINES, **{k: machine[k] for k in sorted(machine)}},
        "category3_without_combined_plan": lost,
        "category3c_gain_by_injection_reason": dict(sorted(gain_by_reason.items())),
        "improved_composition": dict(improved_pieces),
        "saving_among_improved": None if not savings else {
            "n": len(savings), "median": statistics.median(savings),
            "quartiles": statistics.quantiles(savings, n=4), "mean": round(statistics.mean(savings), 2),
            "max": max(savings), "share_saving_one": round(sum(1 for x in savings if x == 1) / len(savings), 4)},
        "worse_seam_difference": {str(k): v for k, v in sorted(seam_diff.items())},
        "stuck_without_plan_combined": dict(sorted(stuck_without_plan_combined.items())),
        "stuck_concentration": {
            "S1": s1, "top": per[:10],
            "top10_share": round(sum(p["stuck"] for p in per[:10]) / s1, 4),
            "top30_share": round(sum(p["stuck"] for p in per[:30]) / s1, 4),
            "repositories_without_long": sum(1 for p in per if p["long"] == 0),
            "repositories_without_stuck": sum(1 for p in per if p["stuck"] == 0),
            "repositories_with_stuck_without_category3c": sum(1 for p in per if p["stuck"] and not p["category3c"]),
            "median_long_per_repository": statistics.median(p["long"] for p in per),
            "median_stuck_per_repository": statistics.median(p["stuck"] for p in per),
            "long_share_of_methods": round(sum(p["long"] for p in per) / sum(p["methods"] for p in per), 4)},
        "per_repository_by_tier": {
            "category3c_over_S1": per_tier_medians(rows, "combined_category.3", "stuck"),
            "S2c_over_S1": per_tier_medians(rows, "stuck_combined", "stuck"),
            "improved_over_slimmable": per_tier_medians(rows, "improved", "slimmable")},
        "readings_of_long_methods": dict(readings_long),
        "officefloor_reading": {"long_methods": sum(of_repos.values()), "repositories": of_repos.most_common(5),
                                "evidence": of_evidence.most_common(5)},
        "unparsed_by_repository": [(n, c) for n, c in unparsed.most_common(8) if c],
        "longest_methods": [{"length": l, "repository": n, "method": m} for l, n, m in longest[:5]],
        "scan_time": {"total_seconds": round(sum(s for s, _ in secs)), "median_seconds": statistics.median(s for s, _ in secs),
                      "longest": secs[:5], "first_finished_utc": finished[0], "last_finished_utc": finished[-1]},
    }
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "posthoc.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: out[k] for k in ("construction_exceptions", "category3c_composition", "improved_composition")}, indent=1)[:1500])
    print(json.dumps(out["test_paths"]["dropped"]), out["test_paths"]["headline"]["H1"],
          out["test_paths"]["headline"]["category3c_over_S1"]["population_interval"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
