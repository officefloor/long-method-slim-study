"""The analysis (docs/ANALYSIS_PLAN.md, sections 5 and 6): the measures, per repository and pooled,
from the raw scans. It counts and pools what OfficeFloorSlim reported; it computes no cost.

    python -m long_method_slim_study.analyse --scans results/scans --sample sample/X.csv \\
        --derivation sample/X.derivation.json --out results/analysis
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import statistics
import sys
from collections import Counter

from long_method_slim_study import pins

STUCK = ("not_slimmable", "slimmable_with_record")
SLIMMABLE = ("slimmable", "slimmable_but_locked")
STATUSES = ("slimmable", "slimmable_but_locked", "slimmable_with_record", "not_slimmable")


def repository(scan: dict) -> dict:
    """One repository's counts, from its scan."""
    status, category, reasons_long, reasons_stuck = Counter(), Counter(), Counter(), Counter()
    slim_costs, pairs, worse = [], [], []
    stuck = stuck_planned = 0
    for m in scan["methods"]:
        s, o = m["sinewslim"], m["officefloor"]
        status[s["status"]] += 1
        if s["status"] in SLIMMABLE and s.get("cost") is not None:
            slim_costs.append(s["cost"])
        is_stuck = s["status"] in STUCK
        if is_stuck:
            stuck += 1
            stuck_planned += 1 if o["feasible"] else 0
            category[str(m["category"]["number"])] += 1
        if not o["feasible"]:
            reasons_long[o["reason"]] += 1
            if is_stuck:
                reasons_stuck[o["reason"]] += 1
        if s.get("cost") is not None and o["feasible"]:
            pair = {"seam": (s["width"], o["worst_seam"]), "parts": (s["pieces"], len(o["functions"])),
                    "largest": (s["largest_piece"], o["largest_function"])}
            pairs.append(pair)
            if o["worst_seam"] > s["width"]:
                worse.append({"path": m["path"], "method": f"{m['type']}.{m['signature']}", "line": m["line"],
                              "sinewslim_width": s["width"], "officefloor_worst_seam": o["worst_seam"]})
    return {"methods": sum(scan["methods_by_reading"].values()), "long": scan["long_methods"],
            "readings": dict(scan["methods_by_reading"]), "status": dict(status), "slim_costs": slim_costs,
            "stuck": stuck, "stuck_planned": stuck_planned, "category": dict(category),
            "reasons_long": dict(reasons_long), "reasons_stuck": dict(reasons_stuck), "pairs": pairs,
            "worse": worse, "unparsed": len(scan["unparsed"])}


def ratio(rows: list[dict], num: str, den: str, weights: dict[str, float] | None = None) -> float | None:
    """Sum over sum; with weights, each repository's counts weighted by its stratum's."""
    w = (lambda r: weights[r["tier"]]) if weights else (lambda r: 1.0)
    n = sum(w(r) * value(r, num) for r in rows)
    d = sum(w(r) * value(r, den) for r in rows)
    return n / d if d else None


def value(r: dict, key: str) -> float:
    if key.startswith("category."):
        return r["category"].get(key.split(".", 1)[1], 0)
    return r[key]


def bootstrap(rows: list[dict], num: str, den: str, weights: dict[str, float] | None, resamples: int,
              seed: int, level: float) -> list[float] | None:
    """A percentile interval, resampling repositories within each stratum."""
    rng = random.Random(seed)
    by_tier: dict[str, list[dict]] = {}
    for r in rows:
        by_tier.setdefault(r["tier"], []).append(r)
    values = []
    for _ in range(resamples):
        sample = [rng.choice(rs) for rs in by_tier.values() for _ in rs]
        v = ratio(sample, num, den, weights)
        if v is not None:
            values.append(v)
    if not values:
        return None
    values.sort()
    lo, hi = (1 - level) / 2, 1 - (1 - level) / 2
    return [round(values[int(lo * (len(values) - 1))], 4), round(values[int(hi * (len(values) - 1))], 4)]


def summarise_pairs(pairs: list[dict], key: str) -> dict:
    a = [p[key][0] for p in pairs]
    b = [p[key][1] for p in pairs]
    return {"n": len(pairs), "officefloor_smaller": sum(1 for x, y in zip(a, b) if y < x),
            "equal": sum(1 for x, y in zip(a, b) if y == x), "officefloor_larger": sum(1 for x, y in zip(a, b) if y > x),
            "median_sinewslim": statistics.median(a) if a else None,
            "median_officefloor": statistics.median(b) if b else None}


def pooled(rows: list[dict]) -> dict:
    def total(key):
        return sum(r[key] for r in rows)

    def merged(key):
        c = Counter()
        for r in rows:
            c.update(r[key])
        return dict(sorted(c.items()))

    costs = sorted(c for r in rows for c in r["slim_costs"])
    pairs = [p for r in rows for p in r["pairs"]]
    return {
        "repositories": len(rows),
        "L1": {"methods": total("methods"), "long": total("long")},
        "L2": {s: sum(r["status"].get(s, 0) for r in rows) for s in STATUSES},
        "L3": None if not costs else {"n": len(costs), "median": statistics.median(costs),
                                       "quartiles": statistics.quantiles(costs, n=4) if len(costs) > 1 else costs,
                                       "max": costs[-1]},
        "S1": total("stuck"), "S2": total("stuck_planned"), "S3": merged("category"),
        "C1": summarise_pairs(pairs, "seam"),
        "C2": {"parts": summarise_pairs(pairs, "parts"), "largest": summarise_pairs(pairs, "largest")},
        "F1": {"long_without_plan": merged("reasons_long"), "stuck_without_plan": merged("reasons_stuck")},
        "R1": merged("readings"),
        "unparsed_files": total("unparsed"),
    }


def per_repository(rows: list[dict], num: str) -> dict:
    """P1: each repository's share, over those with at least one stuck method."""
    shares = sorted(value(r, num) / r["stuck"] for r in rows if r["stuck"])
    return {"repositories": len(shares), "median": round(statistics.median(shares), 4) if shares else None}


def headline(rows: list[dict], weights: dict[str, float]) -> dict:
    out = {}
    for name, num in (("S2_over_S1", "stuck_planned"), ("category3_over_S1", "category.3")):
        out[name] = {
            "pooled": round(ratio(rows, num, "stuck") or 0, 4),
            "interval": bootstrap(rows, num, "stuck", None, pins.BOOTSTRAP_RESAMPLES, pins.BOOTSTRAP_SEED, pins.INTERVAL),
            "population": round(ratio(rows, num, "stuck", weights) or 0, 4),
            "population_interval": bootstrap(rows, num, "stuck", weights, pins.BOOTSTRAP_RESAMPLES, pins.BOOTSTRAP_SEED,
                                             pins.INTERVAL),
            "by_tier": {t: round(ratio([r for r in rows if r["tier"] == t], num, "stuck") or 0, 4)
                        for t in sorted({r["tier"] for r in rows})},
            "per_repository": per_repository(rows, num),
        }
    return out


def weights_from(derivation: dict) -> dict[str, float]:
    """Each stratum's weight, population over usable (the sampler's own advice)."""
    out = {}
    for stratum, s in derivation["summary"]["per_stratum"].items():
        tier = stratum.split("/", 1)[1]
        out[tier] = s["population"] / s["usable"] if s.get("usable") else 0.0
    return out


def analyse(scans_dir: str, sample_csv: str, derivation: dict) -> dict:
    with open(sample_csv, newline="") as f:
        sample = list(csv.DictReader(f))
    usable = {r["full_name"]: r for r in sample if r["status"] == "usable"}
    rows, missing = [], []
    for name, r in usable.items():
        path = os.path.join(scans_dir, name.replace("/", "__") + ".json")
        if not os.path.exists(path):
            missing.append(name)
            continue
        with open(path) as f:
            scan = json.load(f)
        rows.append({"full_name": name, "tier": r["tier"], "commit": r["commit"], **repository(scan)})
    weights = weights_from(derivation)
    return {
        "schema": "long-method-slim-study-analysis/1",
        "sample": {"usable": len(usable), "scanned": len(rows), "not_scanned": sorted(missing),
                   "excluded": sum(1 for r in sample if r["status"] == "excluded"),
                   "error": sum(1 for r in sample if r["status"] == "error")},
        "weights": weights,
        "headline": headline(rows, weights) if rows else None,
        "pooled": pooled(rows),
        "by_tier": {t: pooled([r for r in rows if r["tier"] == t]) for t in sorted({r["tier"] for r in rows})},
        "officefloor_worst_seam_larger": [w | {"repository": r["full_name"]} for r in rows for w in r["worse"]],
        "per_repository": [{k: v for k, v in r.items() if k not in ("pairs", "worse", "slim_costs")} for r in rows],
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scans", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--derivation", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    with open(a.derivation) as f:
        derivation = json.load(f)
    result = analyse(a.scans, a.sample, derivation)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "analysis.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({"sample": result["sample"], "headline": result["headline"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
