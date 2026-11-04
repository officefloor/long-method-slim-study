"""The exploratory reading of the category 4 methods (combined split): what each one is, refined from
the harness's re-read of the source, and whether each kind is spread evenly over the sample or
belongs to a few repositories or kinds of system.

    python -m long_method_slim_study.explore.report --scans results/scans \\
        --sample sample/open-source-repository-sample.csv \\
        --derivation sample/open-source-repository-sample.derivation.json \\
        --harness .tmp/explore/harness --measure .tmp/explore/measure \\
        --meta exploratory/data/repo-meta.json --out exploratory/results/explore.json \\
        --tables exploratory/results/tables.md

Exploratory: none of this was registered, and none of it changes a registered figure. It proposes
the next hypotheses. Population figures use the study's own weights and bootstrap.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict

from long_method_slim_study import analyse
from long_method_slim_study.explore import complexity, domains, rootcause
from long_method_slim_study.explore.harness import blocking_lines
from long_method_slim_study.posthoc import load_rows

LIMITS = ["5", "6", "7", "8", "10"]
SLIMMED = ("SLIMMABLE", "SLIMMABLE_BUT_LOCKED")
LOOPS = ("ForStmt", "ForEachStmt", "WhileStmt", "DoStmt")
# what counts as unexplained after refinement: no reading of the source, or a reading that names nothing
RESIDUAL = {"not re-read", "expression: other", "data: no plan at 10", "unknown statement"}


def method_id(m: dict) -> str:
    return f"{m['path']}:{m['line']}:{m['signature']}"


def load_harness(directory: str) -> dict[str, dict]:
    out = {}
    for path in glob.glob(os.path.join(directory, "*.jsonl")):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                if not r.get("start"):  # OWNER__NAME#chunk.jsonl; a timeout has no result ("not re-read")
                    out[os.path.basename(path)[:-6].split("#")[0] + "|" + r["id"]] = r
    return out


def escaping(j: dict | None) -> int:
    return 0 if not j else j.get("return", 0) + j.get("break", 0) + j.get("continue", 0) + j.get("labelled", 0)


def first_limit(h: dict, key: str, ok) -> str | None:
    for k in LIMITS:
        v = (h.get("limits") or {}).get(k, {}).get(key)
        if v is not None and ok(v):
            return k
    return None


WHERE = {**{k: "a loop" for k in LOOPS}, "TryStmt": "a try", "SwitchStmt": "a switch", "LabeledStmt": "a labelled block",
         "SynchronizedStmt": "a synchronized block", "IfStmt": "an if", "BlockStmt": "a block",
         "ExpressionStmt": "an expression", "ReturnStmt": "a return statement",
         "ExplicitConstructorInvocationStmt": "a constructor call"}


# statements that hold others: a jump inside one can cross a cut between them
COMPOUND = LOOPS + ("IfStmt", "TryStmt", "SwitchStmt", "SynchronizedStmt", "LabeledStmt", "BlockStmt")


def jump_kinds(j: dict) -> str:
    ret = j.get("return", 0) + j.get("yield", 0) > 0
    bc = j.get("break", 0) + j.get("continue", 0) + j.get("labelled", 0) > 0
    return "return and break/continue" if ret and bc else "return" if ret else "break/continue" if bc else "no jump found"


def regroup(group: str, cause: str, h: dict | None) -> tuple[str, str]:
    """A control method the instrument reports for a jump that crosses no cut is not control coupled:
    a constructor whose body is only super(...)/this(...) (the call must stay first); a body of one
    simple statement, such as a single `return <expression>` (no cut between statements, and the
    return is the statement's own end); jumps that belong to a lambda or anonymous class (they end the
    lambda, not a cut); or a one-statement body with no jump at all. These move to indivisible. Needs
    the harness's version 3 fields; an older result is left as it is."""
    if group != "control" or not h or not h.get("found") or "method_all_jumps" not in h:
        return group, cause
    if h.get("constructor_delegation_only"):
        return "indivisible", "constructor delegation (the body is only super(...) or this(...))"
    if h.get("top_statements") == 1 and h.get("only_statement") and h["only_statement"] not in COMPOUND:
        return "indivisible", "a one-statement body (one return or expression)"
    o = h.get("outer")
    every = (o or {}).get("all_jumps") if o else h["method_all_jumps"]
    lam = (o or {}).get("lambda_jumps", 0) if o else h.get("method_lambda_jumps", 0)
    if jump_kinds(every or {}) != "no jump found":
        return group, cause
    if lam:
        return "indivisible", "returns inside a lambda or anonymous class"
    if h.get("top_statements") == 1:
        return "indivisible", "a one-statement body (one return or expression)"
    return group, cause


def refine(group: str, cause: str, h: dict | None) -> tuple[str, dict]:
    """A finer class for one category 4 method, and the facts it rests on."""
    if h is None or not h.get("found"):
        return "not re-read", {}
    stmt = h.get("inner") or h.get("outer") or {}
    facts: dict = {}
    if group == "indivisible":
        if cause == "switch" and "switch" in stmt:
            s = stmt["switch"]
            facts = s
            if s["cases_over_target"]:
                return "switch: a case over the cap", facts
            if s["max_case_lines"] <= 3:
                return "switch: flat table (every case 3 lines or fewer)", facts
            return "switch: short cases (each under the cap, too many together)", facts
        if cause == "if" and "if" in stmt:
            i = dict(stmt["if"], outputs=stmt.get("outputs"), jumps=escaping(stmt.get("jumps")))
            facts = i
            if i["else_if"] >= 2:
                return "if: else-if chain (dispatch)", facts
            out, jump = (i["outputs"] or 0) > 0, i["jumps"] > 0
            if not out and not jump:
                return "if: branchy leaf (no values out, no jumps)", facts
            if out and not jump:
                return "if: passes values on", facts
            if jump and not out:
                return "if: controls flow (jumps out)", facts
            return "if: passes values and jumps", facts
        if cause == "expression" and "expression" in stmt:
            e = stmt["expression"]
            facts = e
            n = max(1, e["lines"])
            big = {k: v for k, v in e["largest"].items() if v >= n / 2}
            for k in ("lambda", "anonymous_class", "array_initializer", "switch_expression", "text_block"):
                if k in big:
                    return f"expression: {k.replace('_', ' ')}", facts
            if e["max_call_chain"] >= 4:
                return "expression: call chain (builder)", facts
            if e["max_string_literals_concatenated"] >= 5:
                return "expression: string concatenation", facts
            if e["max_arguments"] >= 8:
                return "expression: long argument list", facts
            if "conditional" in big:
                return "expression: nested conditionals", facts
            return "expression: other", facts
        if cause in ("loop", "try", "labelled statement", "synchronized block"):
            return f"nested {cause} over the cap", facts
        return cause, facts
    if group == "data":
        k = first_limit(h, "combined", bool)
        if k and k != "5":
            return f"data: plan at {k}", {"combined_at": k}
        kb = first_limit(h, "body", lambda v: v in SLIMMED)
        if kb and kb != "5":
            return f"data: blocking body slims at {kb} (inner limit)", {"body_at": kb}
        return "data: no plan at 10", {}
    if group == "control":
        o = h.get("outer") or {}
        outer = o.get("kind")
        top = not outer
        leaving = (o.get("jumps") if outer else h.get("method_jumps")) or {}
        every = (o.get("all_jumps") if outer else h.get("method_all_jumps")) or {}
        what = jump_kinds(leaving)
        if what == "no jump found" and jump_kinds(every) != "no jump found":
            # no jump leaves the statement, but one inside it targets a loop or switch nested in it,
            # so it still crosses a cut between that nested statement's own statements
            what = "nested " + jump_kinds(every)
        where = "the top level" if top else WHERE.get(outer, f"a {outer}")
        return f"control: {what}, in {where}", {"container": outer, "jumps": leaving, "all_jumps": every}
    return cause, facts


def gini(xs: list[float]) -> float:
    xs = sorted(xs)
    n, s = len(xs), sum(xs)
    return round(sum((2 * i - n + 1) * x for i, x in enumerate(xs)) / (n * s), 3) if s else 0.0


def concentration(per_repo: Counter, long: dict[str, int], hot: set[str]) -> dict:
    """How a set of methods is spread over the repositories, against their long methods."""
    total, L = sum(per_repo.values()), sum(long.values())
    if not total:
        return {"n": 0}
    p = total / L
    with_long = [n for n in long if long[n]]
    chi = sum((per_repo[n] - long[n] * p) ** 2 / (long[n] * p * (1 - p)) for n in with_long) if p < 1 else 0
    top10 = per_repo.most_common(10)
    return {"n": total, "repositories": len(per_repo),
            "top1": top10[0], "top10_share": round(sum(v for _, v in top10) / total, 4),
            "top10_long_share": round(sum(long[n] for n, _ in top10) / L, 4),
            "hot_share": round(sum(per_repo[n] for n in hot) / total, 4),
            "dispersion_index": round(chi / (len(with_long) - 1), 1)}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("scans", "sample", "derivation", "harness", "meta", "out"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--tables", help="also write the tables as Markdown here")
    ap.add_argument("--measure", help="the forked measurer's output (explore.measure run): divergence and complexity")
    a = ap.parse_args(argv)
    with open(a.derivation) as f:
        weights = analyse.weights_from(json.load(f))
    scans = load_rows(a.scans, a.sample)
    harness = load_harness(a.harness)
    with open(a.meta) as f:
        meta = json.load(f)["repositories"]
    coded = {n: domains.domain(meta.get(n, {}), n) for n, _, _ in scans}

    long, c4 = {}, Counter()
    by_group, by_cause, by_class = Counter(), Counter(), Counter()
    repo_class, repo_group = defaultdict(Counter), defaultdict(Counter)
    class_facts = defaultdict(list)
    limits_all = {k: Counter() for k in LIMITS}
    reread = 0
    method_class, statements = {}, {}
    for name, tier, scan in scans:
        key = name.replace("/", "__")
        long[name] = len(scan["methods"])
        for m in scan["methods"]:
            if not rootcause.is_category4(m):
                continue
            g, cause = rootcause.root(m["combined"])
            h = harness.get(key + "|" + method_id(m))
            g, cause = regroup(g, cause, h)
            reread += 1 if h and h.get("found") else 0
            cls, facts = refine(g, cause, h)
            mk = key + "|" + method_id(m)
            method_class[mk] = (g, cls)
            outer, inner = blocking_lines(m["combined"].get("detail"))
            at, st = (inner, (h or {}).get("inner")) if inner else (outer, (h or {}).get("outer"))
            if at and st and "inputs" in st:
                statements[mk] = {"lo": at["start"], "hi": at["end"], "inputs": st["inputs"]}
            c4[name] += 1
            by_group[g] += 1
            by_cause[(g, cause)] += 1
            by_class[(g, cls)] += 1
            repo_class[(g, cls)][name] += 1
            repo_group[g][name] += 1
            if facts:
                class_facts[(g, cls)].append(facts)
            if h and h.get("found"):
                for k in LIMITS:
                    v = h["limits"][k]
                    limits_all[k]["combined"] += v["combined"]
                    limits_all[k]["conventional"] += v["conventional"] in SLIMMED
                    limits_all[k]["injection"] += v["injection"]

    L, C = sum(long.values()), sum(c4.values())
    p = C / L
    hot = {n for n in long if long[n] and (c4[n] - long[n] * p) / math.sqrt(long[n] * p * (1 - p)) > 3.9}

    # check: at limit 5 the harness reproduces the scan (category 4: no combined plan)
    check = {"reread": reread, "combined_plan_at_5": limits_all["5"]["combined"]}

    # domains: category 4 per long method, by domain, weighted, with intervals
    rows = []
    for name, tier, scan in scans:
        r = {"full_name": name, "tier": tier, "long": long[name], "c4": c4[name],
             "residual": sum(v[name] for (g, c), v in repo_class.items() if c in RESIDUAL)}
        for g in ("indivisible", "data", "control"):
            r[g] = repo_group[g][name]
        rows.append(r)
    by_domain = {}
    for d in sorted({d for d, _ in coded.values()}):
        sub = [r for r in rows if coded[r["full_name"]][0] == d]
        f = analyse.figure(sub, weights, "c4", "long")
        by_domain[d] = {"repositories": len(sub), "long": sum(r["long"] for r in sub), "c4": f["count"],
                        "pooled": f["pooled"], "population": f["population"], "interval": f["population_interval"],
                        "groups": {g: sum(r[g] for r in sub) for g in ("indivisible", "data", "control")},
                        "residual": sum(r["residual"] for r in sub)}
    overall = analyse.figure(rows, weights, "c4", "long")

    def summarise(facts: list[dict]) -> dict:
        out = {}
        for k in ("entries", "labels", "max_case_lines", "median_case_lines", "branches", "else_if", "lines",
                  "max_call_chain", "max_arguments"):
            xs = [f[k] for f in facts if isinstance(f.get(k), (int, float))]
            if xs:
                out[k] = {"median": statistics.median(xs), "max": max(xs)}
        for k in ("fallthrough", "returning", "in_loop"):
            xs = [f[k] for f in facts if k in f]
            if xs:
                out[f"share_with_{k}"] = round(sum(1 for x in xs if x) / len(xs), 4)
        return out

    out = {
        "schema": "long-method-slim-study-explore/1",
        "status": "exploratory: not registered; changes no registered figure; for the next hypotheses",
        "category4": C, "long": L, "check": check,
        "groups": {g: {**concentration(repo_group[g], long, hot), "n": v, "share": round(v / C, 4)}
                   for g, v in by_group.most_common()},
        "causes": {f"{g} / {c}": v for (g, c), v in by_cause.most_common()},
        "classes": {f"{g} / {c}": {**concentration(repo_class[(g, c)], long, hot), "n": v, "share": round(v / C, 4),
                                   "facts": summarise(class_facts[(g, c)])}
                    for (g, c), v in by_class.most_common()},
        "residual": {"definition": sorted(RESIDUAL),
                     **concentration(Counter({n: r["residual"] for r in rows for n in [r["full_name"]]
                                              if r["residual"]}), long, hot)},
        "limits": {"note": "of the category 4 methods re-read, how many have a plan when the limit of 5 is raised "
                           "to k (combined: the combined split's carried values; conventional: SinewSlim's "
                           "max_inputs; injection: the injection split's carried values)",
                   **{k: dict(v) for k, v in limits_all.items()}},
        "concentration": {**concentration(c4, long, hot), "hot_repositories": len(hot),
                          "hot_long_share": round(sum(long[n] for n in hot) / L, 4),
                          "hot": sorted(hot, key=lambda n: (-c4[n], n))},
        "domains": {"overall": {"pooled": overall["pooled"], "population": overall["population"],
                                "interval": overall["population_interval"]},
                    "by_domain": by_domain,
                    "coding": {n: {"domain": d, "keyword": k} for n, (d, k) in sorted(coded.items())}},
    }
    if a.measure:
        measured = complexity.load(a.measure)
        out["complexity"] = complexity.analyse(scans, measured, method_class, statements)
        # sensitivity: a repository whose call resolution ran out of its budget undercounts its internal
        # calls (so leans to catchment); the same reading without those repositories
        within = {k: v for k, v in measured.items() if not v["budget_exhausted"]}
        out["complexity_within_budget"] = complexity.analyse(scans, within, method_class, statements)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, default=list)
    if a.tables:
        with open(a.tables, "w") as f:
            f.write(tables(out))
    print(json.dumps({k: out[k] for k in ("category4", "check")}), f"-> {a.out}")
    return 0


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def tables(o: dict) -> str:
    """The report's tables, as Markdown: every number from explore.json, none typed by hand."""
    C = o["category4"]
    lines = ["# Exploratory tables: the category 4 methods", "",
             "Generated by `long_method_slim_study.explore.report` from `explore.json`. Exploratory: not "
             "registered, and no registered figure changes. Category 4 = stuck, and no plan from the combined "
             f"split: {C:,} methods. Re-read from source: {o['check']['reread']:,}; with a combined plan at the "
             f"scan's limit of 5: {o['check']['combined_plan_at_5']} (the harness reproduces the scan).", "",
             "Concentration columns: *repos* holding any; *top 10* their share of the class, beside the same "
             "repositories' share of all long methods (what size alone predicts); *hot* the share in the "
             f"{o['concentration']['hot_repositories']} repositories whose category 4 rate is significantly "
             f"above the pooled rate (they hold {pct(o['concentration']['hot_long_share'])} of the long methods); "
             "*dispersion* 1 when spread as the long methods are, higher when clustered.", "",
             "## Root cause, refined", "",
              "Groups as `explore/rootcause.py` reads the instrument's reasons, except that a control method with no "
              "jump crossing a cut (a constructor that only delegates, a body of one return or expression, jumps that belong to a lambda) is "
              "moved to indivisible (`report.regroup`). A *nested* jump targets a loop or switch inside the blocking "
              "statement: it leaves no statement, but crosses a cut inside it.", "",
             "| Class | Methods | Share | Repos | Top 10 | Top 10 by size | Hot | Dispersion |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for g, v in o["groups"].items():
        lines.append(f"| **{g}** | **{v['n']:,}** | **{pct(v['share'])}** | {v['repositories']} | "
                     f"{pct(v['top10_share'])} | {pct(v['top10_long_share'])} | {pct(v['hot_share'])} | "
                     f"{v['dispersion_index']} |")
        for k, c in o["classes"].items():
            if k.startswith(g + " / "):
                lines.append(f"| &nbsp;&nbsp;{k.split(' / ', 1)[1]} | {c['n']:,} | {pct(c['share'])} | "
                             f"{c['repositories']} | {pct(c['top10_share'])} | {pct(c['top10_long_share'])} | "
                             f"{pct(c['hot_share'])} | {c['dispersion_index']} |")
    r = o["residual"]
    lines += ["", f"**Residual** ({', '.join(r['definition'])}): {r['n']:,} methods "
              f"({pct(r['n'] / C)}), in {r['repositories']} repositories; top 10 hold {pct(r['top10_share'])} "
              f"(size predicts {pct(r['top10_long_share'])}); hot {pct(r['hot_share'])}; dispersion "
              f"{r['dispersion_index']}; most in {r['top1'][0]} ({r['top1'][1]}).", "",
              "## The limit of 5 raised", "", o["limits"]["note"] + ".", "",
              "| Limit | Combined split has a plan | SinewSlim slims | Injection split has a plan |",
              "|---:|---:|---:|---:|"]
    n = o["check"]["reread"]
    for k in LIMITS:
        v = o["limits"][k]
        lines.append(f"| {k} | {v.get('combined', 0):,} ({pct(v.get('combined', 0) / n)}) | "
                     f"{v.get('conventional', 0):,} ({pct(v.get('conventional', 0) / n)}) | "
                     f"{v.get('injection', 0):,} ({pct(v.get('injection', 0) / n)}) |")
    d = o["domains"]
    ov = d["overall"]
    lines += ["", "## By domain", "",
              "Category 4 methods per long method, population-weighted with the study's bootstrap interval; "
              f"overall {pct(ov['population'])} ({pct(ov['interval'][0])} to {pct(ov['interval'][1])}). Domains "
              "coded by keyword rules from each repository's GitHub description and topics "
              "(`explore/domains.py`): crude, reviewable, the coding listed in `explore.json`.", "",
              "| Domain | Repos | Long methods | Category 4 | Rate (interval) | Indivisible | Data | Control | Residual |",
              "|---|---:|---:|---:|---|---:|---:|---:|---:|"]
    for name, v in sorted(d["by_domain"].items(), key=lambda t: -t[1]["population"]):
        c4 = max(1, v["c4"])
        lines.append(f"| {name} | {v['repositories']} | {v['long']:,} | {v['c4']:,} | {pct(v['population'])} "
                     f"({pct(v['interval'][0])} to {pct(v['interval'][1])}) | {pct(v['groups']['indivisible'] / c4)} | "
                     f"{pct(v['groups']['data'] / c4)} | {pct(v['groups']['control'] / c4)} | "
                     f"{pct(v['residual'] / c4)} |")
    if "complexity" in o:
        lines += complexity_tables(o["complexity"])
    if o.get("complexity_within_budget") and o["complexity"]["budget_exhausted"]:
        lines += budget_table(o["complexity"], o["complexity_within_budget"])
    coding = d["coding"]
    lines += ["", "## The hot repositories", "", "| Repository | Domain |", "|---|---|"]
    lines += [f"| {n} | {coding[n]['domain']} |" for n in o["concentration"]["hot"]]
    return "\n".join(lines) + "\n"



def complexity_tables(x: dict) -> list[str]:
    def roles(r):
        return " / ".join(pct(r[k]) for k in ("catchment", "pipe", "junction")) if r else "-"

    lines = ["", "## Coupling divergence and complexity", "",
             f"The concentration-divergence study's measurer (tag analysis-v1, forked to record call lines), over "
             f"the {x['repositories_measured']} cloned repositories. Divergence: {x['definition']}. Roles shown as "
             "catchment / pipe / junction. Complexity grows with length, so each group is also shown "
             "*standardised*: its means within length bins, weighted to category 4's length distribution.", "",
             "| Group | Long methods | Joined | Median length | Median cognitive | Median cc | Roles |"
             " Standardised cognitive | Standardised cc | Standardised cognitive per line | Standardised roles |",
             "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|"]
    for g, v in x["groups"].items():
        s = v.get("standardised") or {}
        lines.append(f"| {g} | {v['wanted']:,} | {v['joined']:,} | {v.get('length', '-')} | {v.get('cognitive', '-')} | "
                     f"{v.get('cc', '-')} | {roles(v.get('roles'))} | {s.get('cognitive', '-')} | {s.get('cc', '-')} | "
                     f"{s.get('cognitive_per_line', '-')} | {roles(s.get('roles'))} |")
    lines += ["", "By length bin (median cognitive; roles):", "",
              "| Bin | " + " | ".join(x["groups"]) + " |", "|---|" + "---|" * len(x["groups"])]
    bins = list(x["length_weights"])
    for b in bins:
        cells = []
        for g, v in x["groups"].items():
            r = v["by_bin"].get(b)
            cells.append(f"n={r['n']:,}, cog {r['cognitive']}, {roles(r['roles'])}" if r else "-")
        lines.append(f"| {b} | " + " | ".join(cells) + " |")
    lines += ["", "Category 4 by refined class: the method's role, and the blocking statement's (taken as a method "
              "of its own: in = 1 + its inputs, out = the internal calls inside it).", "",
              "| Class | Joined | Median length | Median cognitive | Cognitive per line | Method roles |"
              " Statements | Statement roles |", "|---|---:|---:|---:|---:|---|---:|---|"]
    for k, v in x["category4_classes"].items():
        if v.get("n", 0) >= 10:
            lines.append(f"| {k} | {v['n']:,} | {v['length']} | {v['cognitive']} | {v['cognitive_per_line']} | "
                         f"{roles(v['roles'])} | {v['statement_n']:,} | {roles(v['statement_roles'])} |")
    if x["budget_exhausted"]:
        lines += ["", f"Repositories whose call resolution ran out of its budget: {', '.join(x['budget_exhausted'])}."]
    return lines


def budget_table(full: dict, within: dict) -> list[str]:
    """Roles and standardised complexity with and without the repositories that ran out of budget."""
    def roles(r):
        return " / ".join(pct(r[k]) for k in ("catchment", "pipe", "junction")) if r else "-"

    lines = ["", "### Without the repositories that ran out of budget", "",
             f"Sensitivity: {', '.join(full['budget_exhausted'])} left calls unattempted when their hour ran out, so "
             "their internal calls are undercounted (leaning to catchment). The same reading without them:", "",
             "| Group | Joined (all) | Roles (all) | Joined (within budget) | Roles (within budget) |"
             " Standardised roles (within budget) | Standardised cognitive (within budget) |",
             "|---|---:|---|---:|---|---|---:|"]
    for g, v in full["groups"].items():
        w = within["groups"][g]
        lines.append(f"| {g} | {v['joined']:,} | {roles(v.get('roles'))} | {w['joined']:,} | {roles(w.get('roles'))} | "
                     f"{roles((w.get('standardised') or {}).get('roles'))} | "
                     f"{(w.get('standardised') or {}).get('cognitive', '-')} |")
    lines += ["", "| Category 4 class | Statement roles (all) | Statements (within budget) | Statement roles (within budget) |",
              "|---|---|---:|---|"]
    for k, v in full["category4_classes"].items():
        w = within["category4_classes"].get(k) or {}
        if v.get("statement_n", 0) >= 10:
            lines.append(f"| {k} | {roles(v['statement_roles'])} | {w.get('statement_n', 0):,} | "
                         f"{roles(w.get('statement_roles'))} |")
    return lines


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
