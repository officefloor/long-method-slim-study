#!/usr/bin/env python3
"""Every number and table the paper prints, from the registered analysis and the post hoc readings.

Reads   results/analysis/analysis.json     the registered analysis (docs/ANALYSIS_PLAN.md, sections 5 and 6; step 4)
        results/analysis/posthoc.json      the post hoc readings (long_method_slim_study/posthoc.py; step 5), labelled so
        sample/open-source-repository-sample.derivation.json   the sampler's frame and strata
Writes  paper/generated/numbers.tex        one \\newcommand per number
        paper/generated/tab_*.tex          every table the paper places

Run from the repository root:  .venv/bin/python paper/scripts/numbers.py
No number this study computes is typed into the paper by hand; the only typed numbers are the plan's own
constants (the trigger, the target, the quarter, the seed, the dates) and what the plan records as seen before
registration. If this script's output ever disagrees with the prose, the script is the authority.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "paper", "generated")

macros: dict[str, str] = {}


def load(path):
    with open(os.path.join(ROOT, path)) as f:
        return json.load(f)


def define(name: str, value) -> None:
    if not re.fullmatch(r"[A-Za-z]+", name):
        raise ValueError(f"macro name must be letters only: {name}")
    if name in macros:
        raise ValueError(f"macro defined twice: {name}")
    macros[name] = str(value)


def count(n) -> str:
    return f"{int(round(n)):,}".replace(",", "{,}")


def pct(v, d=1) -> str:
    return f"{100 * v:.{d}f}\\%"


def pctn(v, d=1) -> str:  # a percentage without its sign, for "22.2 to 24.3%"
    return f"{100 * v:.{d}f}"


def dec(v, d=1) -> str:
    return f"{v:.{d}f}"


def interval(iv, d=1) -> str:  # for a table cell, under a "(95% CI)" header
    return f"({pctn(iv[0], d)} to {pctn(iv[1], d)})"


def ci(v, iv, d=1) -> str:  # for prose: the estimate with its interval spelt out
    return f"{pct(v, d)} (95\\% CI {pctn(iv[0], d)} to {pctn(iv[1], d)})"


def minutes(seconds) -> str:
    m = int(round(seconds / 60))
    return f"{m}~min"


def repo(name: str) -> str:
    """A repository name in a macro: underscores escaped, a break allowed after the slash."""
    return name.replace("/", r"/\allowbreak ")


def write(name: str, text: str) -> None:
    with open(os.path.join(OUT, name), "w") as f:
        f.write(text)


# ---------------------------------------------------------------------------------------------
A = load("results/analysis/analysis.json")
P = load("results/analysis/posthoc.json")
D = load("sample/open-source-repository-sample.derivation.json")
H, POOL, TIERS = A["headline"], A["pooled"], A["by_tier"]
TIER_ORDER = ("high", "mid", "low")
TIER_NAME = {"high": "High", "mid": "Mid", "low": "Low"}
TIER_STARS = {"high": "over 5{,}000", "mid": "1{,}000 to 5{,}000", "low": "200 to 999"}

# --- the sample -------------------------------------------------------------------------------
S = D["summary"]
define("nDrawn", count(S["drawn"]))
define("nUsable", count(S["usable"]))
define("nExcluded", count(S["excluded"]))
define("nError", count(S["error"]))
define("nScanned", count(A["sample"]["scanned"]))
define("nNotScanned", count(len(A["sample"]["not_scanned"])))
rows = []
for t in TIER_ORDER:
    s = S["per_stratum"][f"java/{t}"]
    define(f"pop{TIER_NAME[t]}", count(s["population"]))
    define(f"usable{TIER_NAME[t]}", count(s["usable"]))
    define(f"weight{TIER_NAME[t]}", dec(A["weights"][t], 1))
    rows.append(f"{TIER_NAME[t]} & {TIER_STARS[t]} & {count(s['population'])} & {count(s['drawn'])} & "
                f"{count(s['usable'])} & {count(s['excluded'])} & {dec(A['weights'][t], 1)} \\\\")
define("sampleFracHigh", pct(S["per_stratum"]["java/high"]["drawn"] / S["per_stratum"]["java/high"]["population"], 0))
write("tab_sample.tex", "\n".join([
    r"\begin{tabular}{llrrrrr}", r"\toprule",
    r"Tier & Stars & Population & Drawn & Usable & Excluded & Weight \\", r"\midrule", *rows, r"\midrule",
    f"All & & {count(sum(S['per_stratum'][f'java/{t}']['population'] for t in TIER_ORDER))} & {count(S['drawn'])} & "
    f"{count(S['usable'])} & {count(S['excluded'])} & \\\\",
    r"\bottomrule", r"\end{tabular}", ""]))

# --- the corpus (L1, L2, L3) --------------------------------------------------------------------
define("nMethods", count(POOL["L1"]["methods"]))
define("nLong", count(POOL["L1"]["long"]))
define("longShare", pct(POOL["L1"]["long"] / POOL["L1"]["methods"]))
define("nUnparsed", count(POOL["unparsed_files"]))
L2 = POOL["L2"]
slims = L2["slimmable"] + L2["slimmable_but_locked"]
define("nSlimmable", count(L2["slimmable"]))
define("nLocked", count(L2["slimmable_but_locked"]))
define("nRecord", count(L2["slimmable_with_record"]))
define("nNotSlimmable", count(L2["not_slimmable"]))
define("nSlims", count(slims))
define("slimsShare", pct(slims / POOL["L1"]["long"]))
define("nStuck", count(POOL["S1"]))
define("stuckShare", pct(POOL["S1"] / POOL["L1"]["long"]))
define("recordShareOfStuck", pct(L2["slimmable_with_record"] / POOL["S1"]))
define("slimCostMedian", count(POOL["L3"]["median"]))
define("slimCostQone", count(POOL["L3"]["quartiles"][0]))
define("slimCostQthree", count(POOL["L3"]["quartiles"][2]))
define("slimCostMax", count(POOL["L3"]["max"]))
STATUS_NAME = [("slimmable", "Slimmable"), ("slimmable_but_locked", "Slimmable, but locked to its class"),
               ("slimmable_with_record", "Slimmable only with a record (stuck)"), ("not_slimmable", "Not slimmable (stuck)")]
rows = []
for key, label in STATUS_NAME:
    cells = " & ".join(count(TIERS[t]["L2"][key]) for t in TIER_ORDER)
    rows.append(f"{label} & {cells} & {count(L2[key])} & {pct(L2[key] / POOL['L1']['long'])} \\\\")
write("tab_status.tex", "\n".join([
    r"\begin{tabular}{lrrrrr}", r"\toprule",
    r"SinewSlim's status & High & Mid & Low & All & Share \\", r"\midrule",
    f"Methods with a body & {' & '.join(count(TIERS[t]['L1']['methods']) for t in TIER_ORDER)} & {count(POOL['L1']['methods'])} & \\\\",
    f"Long (26 code lines or more) & {' & '.join(count(TIERS[t]['L1']['long']) for t in TIER_ORDER)} & {count(POOL['L1']['long'])} & {pct(POOL['L1']['long'] / POOL['L1']['methods'])} of methods \\\\",
    r"\midrule", *rows, r"\midrule",
    f"Stuck (S1) & {' & '.join(count(TIERS[t]['S1']) for t in TIER_ORDER)} & {count(POOL['S1'])} & {pct(POOL['S1'] / POOL['L1']['long'])} of long \\\\",
    r"\bottomrule", r"\end{tabular}", ""]))

# --- the headline figures -----------------------------------------------------------------------
FIG = [("S2_over_S1", "StuckPlanned", "Stuck with an injection-split plan (S2 over S1)"),
       ("category3_over_S1", "CatThree", "Category 3 under the injection split (S3 over S1)"),
       ("S2c_over_S1", "StuckPlannedC", "Stuck with a combined-split plan (S2c over S1)"),
       ("category3c_over_S1", "CatThreeC", "Category 3 under the combined split (S3c over S1): \\textbf{H1}"),
       ("improved_over_slimmable", "Improved", "Improved: injection chosen and cheaper, over what SinewSlim slims (K2): \\textbf{H2}"),
       ("tied_over_slimmable", "Tied", "Tied on the sum, settled by the tie-break (K2)")]
rows, tier_rows = [], []
for key, name, label in FIG:
    f = H[key]
    define(f"n{name}", count(f["count"]))
    define(f"of{name}", count(f["of"]))
    define(f"pooled{name}", pct(f["pooled"]))
    define(f"pop{name}", pct(f["population"]))
    define(f"lo{name}", pctn(f["population_interval"][0]))
    define(f"hi{name}", pctn(f["population_interval"][1]))
    define(f"sampleLo{name}", pctn(f["interval"][0]))
    define(f"sampleHi{name}", pctn(f["interval"][1]))
    define(f"median{name}", pct(f["per_repository"]["median"]))
    define(f"repos{name}", count(f["per_repository"]["repositories"]))
    define(f"ci{name}", ci(f["population"], f["population_interval"]))
    for t in TIER_ORDER:
        define(f"tier{TIER_NAME[t]}{name}", pct(f["by_tier"][t]))
    rows.append(f"{label} & {count(f['count'])} / {count(f['of'])} & {pct(f['pooled'])} & {pct(f['population'])} {interval(f['population_interval'])} & "
                f"{pct(f['per_repository']['median'])} & {count(f['per_repository']['repositories'])} \\\\")
    tier_rows.append(f"{label} & {' & '.join(pct(f['by_tier'][t]) for t in TIER_ORDER)} \\\\")
write("tab_headline.tex", "\n".join([
    r"\begin{tabular}{>{\raggedright\arraybackslash}p{4.7cm}rrlrr}", r"\toprule",
    r"Figure & Count / of & Pooled & Population (95\% CI) & Median & Repos. \\", r"\midrule",
    *rows, r"\bottomrule", r"\end{tabular}", ""]))
write("tab_headline_tiers.tex", "\n".join([
    r"\begin{tabular}{>{\raggedright\arraybackslash}p{8.4cm}rrr}", r"\toprule",
    r"Figure & High & Mid & Low \\", r"\midrule",
    *tier_rows, r"\bottomrule", r"\end{tabular}", ""]))
define("hOneReading", H["H1"]["reading"])
define("hTwoReading", H["H2"]["reading"])
define("hOneBar", pct(H["H1"]["share"], 0))
define("hOneMinimum", count(H["H1"]["minimum"]))
# the per-tier per-repository medians (post hoc)
for key, name in (("category3c_over_S1", "CatThreeC"), ("S2c_over_S1", "StuckPlannedC"), ("improved_over_slimmable", "Improved")):
    for t in TIER_ORDER:
        define(f"tierMedian{TIER_NAME[t]}{name}", pct(P["per_repository_by_tier"][key][t]["median"]))

# --- the categories (S3, S3c) -------------------------------------------------------------------
CAT = [("1", "1: slims by extraction once its jumps are ignored (conventionally fixable)"),
       ("2", "2: slims by extraction with a record"),
       ("3", "3: a plan under the OfficeFloor column only (the rescue)"),
       ("4", "4: no plan from either (needs a redesign)")]
rows = []
for k, label in CAT:
    a, c = POOL["S3"].get(k, 0), POOL["S3c"].get(k, 0)
    define(f"cat{'One Two Three Four'.split()[int(k) - 1]}", count(a))
    define(f"cat{'One Two Three Four'.split()[int(k) - 1]}C", count(c))
    define(f"cat{'One Two Three Four'.split()[int(k) - 1]}Share", pct(a / POOL["S1"]))
    define(f"cat{'One Two Three Four'.split()[int(k) - 1]}CShare", pct(c / POOL["S1"]))
    rows.append(f"{label} & {count(a)} & {pct(a / POOL['S1'])} & {count(c)} & {pct(c / POOL['S1'])} \\\\")
write("tab_categories.tex", "\n".join([
    r"\begin{tabular}{>{\raggedright\arraybackslash}p{8.2cm}rrrr}", r"\toprule",
    r"Category of a stuck method & \multicolumn{2}{c}{Injection split} & \multicolumn{2}{c}{Combined split} \\",
    r" & Count & of S1 & Count & of S1 \\", r"\midrule", *rows, r"\midrule",
    f"Stuck methods (S1) & {count(POOL['S1'])} & & {count(POOL['S1'])} & \\\\",
    r"\bottomrule", r"\end{tabular}", ""]))
define("catThreeGain", count(POOL["S3c"]["3"] - POOL["S3"]["3"]))
G = P["category3c_gain_by_injection_reason"]
REASON_WORD = {"loop": "a loop", "long_statement": "a long statement", "try": "a try", "switch": "a switch",
               "carried": "carried values", "jumps": "a jump"}
define("catThreeGainReasons", ", ".join(f"{REASON_WORD[k]} ({count(v)})" for k, v in sorted(G.items(), key=lambda kv: -kv[1])))
define("nStuckPlannedGain", count(POOL["S2c"] - POOL["S2"]))
define("catOneTwoShare", pct((POOL["S3"]["1"] + POOL["S3"]["2"]) / POOL["S1"]))
define("plannedButConventional", count(POOL["S2c"] - POOL["S3c"]["3"]))
define("plannedButConventionalShare", pct((POOL["S2c"] - POOL["S3c"]["3"]) / POOL["S2c"]))

# --- the reasons (F1, K1) -----------------------------------------------------------------------
REASON = [("loop", "A loop longer than the target"), ("long_statement", "A single statement longer than the target"),
          ("try", "A try with resources or a finally"), ("switch", "A switch whose cases fall through"),
          ("carried", "More than 5 carried values in every plan"), ("jumps", "A jump crossing every cut")]
F1s, F1l, Kc, Kcs = POOL["F1"]["stuck_without_plan"], POOL["F1"]["long_without_plan"], POOL["K1"]["without_plan"], P["stuck_without_plan_combined"]
tot = (sum(F1s.values()), sum(F1l.values()), sum(Kcs.values()), sum(Kc.values()))
rows = []
for k, label in REASON:
    rows.append(f"{label} & {count(F1s.get(k, 0))} & {pct(F1s.get(k, 0) / tot[0])} & {count(F1l.get(k, 0))} & "
                f"{count(Kcs.get(k, 0))} & {pct(Kcs.get(k, 0) / tot[2])} & {count(Kc.get(k, 0))} \\\\")
write("tab_reasons.tex", "\n".join([
    r"\begin{tabular}{>{\raggedright\arraybackslash}p{5.4cm}rrrrrr}", r"\toprule",
    r"Reason & \multicolumn{3}{c}{Injection split} & \multicolumn{3}{c}{Combined split} \\",
    r" & Stuck & Share & All long & Stuck & Share & All long \\", r"\midrule", *rows, r"\midrule",
    f"Without a plan & {count(tot[0])} & & {count(tot[1])} & {count(tot[2])} & & {count(tot[3])} \\\\",
    r"\bottomrule", r"\end{tabular}", ""]))
define("nStuckNoPlan", count(tot[0]))
define("nLongNoPlan", count(tot[1]))
define("nStuckNoPlanC", count(tot[2]))
define("nLongNoPlanC", count(tot[3]))
define("loopShareStuckNoPlan", pct(F1s["loop"] / tot[0]))
define("loopShareStuckNoPlanC", pct(Kcs["loop"] / tot[2]))
define("jumpsStuckNoPlan", count(F1s["jumps"]))
define("jumpsStuckNoPlanC", count(Kcs["jumps"]))
define("nLongPlanC", count(POOL["K1"]["long_with_plan"]))
define("nInjectionUsed", count(POOL["K1"]["injection_used"]))
define("nExtractionOnly", count(POOL["K1"]["extraction_only"]))
define("injectionUsedShareOfPlans", pct(POOL["K1"]["injection_used"] / POOL["K1"]["long_with_plan"]))

# --- the shape (C1, C2) -------------------------------------------------------------------------
C1, C2p, C2l = POOL["C1"], POOL["C2"]["parts"], POOL["C2"]["largest"]
define("nBoth", count(C1["n"]))


def shape_row(label, c, a_name, b_name):
    n = c["n"]
    return (f"{label}: SinewSlim's {a_name} against the split's {b_name} & {count(c['officefloor_smaller'])} ({pct(c['officefloor_smaller'] / n)}) & "
            f"{count(c['equal'])} ({pct(c['equal'] / n)}) & {count(c['officefloor_larger'])} ({pct(c['officefloor_larger'] / n)}) & "
            f"{count(c['median_sinewslim'])} & {count(c['median_officefloor'])} \\\\")


write("tab_shape.tex", "\n".join([
    r"\begin{tabular}{>{\raggedright\arraybackslash}p{5.6cm}rrrrr}", r"\toprule",
    r"Term & Split smaller & Equal & Split larger & \multicolumn{2}{c}{Median} \\",
    r" & & & & SinewSlim & Split \\", r"\midrule",
    shape_row("Worst seam (C1)", C1, "widest piece", "most carried values"),
    shape_row("Parts (C2)", C2p, "pieces", "functions"),
    shape_row("Largest part (C2)", C2l, "largest piece", "largest function"),
    r"\bottomrule", r"\end{tabular}", ""]))
for key, c in (("Seam", C1), ("Parts", C2p), ("Largest", C2l)):
    define(f"splitSmaller{key}", pct(c["officefloor_smaller"] / c["n"]))
    define(f"equal{key}", pct(c["equal"] / c["n"]))
    define(f"splitLarger{key}", pct(c["officefloor_larger"] / c["n"]))
    define(f"medianSinew{key}", count(c["median_sinewslim"]))
    define(f"medianSplit{key}", count(c["median_officefloor"]))
define("nWorse", count(len(A["officefloor_worst_seam_larger"])))
W = P["worse_seam_difference"]
wt = sum(W.values())
define("worseByOne", count(W.get("1", 0)))
define("worseByOneShare", pct(W.get("1", 0) / wt))
define("worseByTwo", count(W.get("2", 0)))
define("worseByThreePlus", count(sum(v for k, v in W.items() if int(k) >= 3)))
define("worseMax", count(max(int(k) for k in W)))

# --- the combined split where extraction would do (K2) -------------------------------------------
K2 = POOL["K2"]
sav = {int(k): v for k, v in K2["saving"].items()}
define("nTiedK", count(K2["tied"]))
define("notImprovedShare", pct((K2["slimmable"] - K2["improved"] - K2["tied"]) / K2["slimmable"]))
define("nNotImproved", count(K2["slimmable"] - K2["improved"] - K2["tied"]))
SV = P["saving_among_improved"]
define("savingMedian", count(SV["median"]))
define("savingQone", count(SV["quartiles"][0]))
define("savingQthree", count(SV["quartiles"][2]))
define("savingMean", dec(SV["mean"], 1))
define("savingMax", count(SV["max"]))
define("savingOneShare", pct(SV["share_saving_one"]))
bands = [("0 (tied)", lambda k: k == 0), ("1", lambda k: k == 1), ("2", lambda k: k == 2), ("3", lambda k: k == 3),
         ("4 or 5", lambda k: k in (4, 5)), ("6 to 10", lambda k: 6 <= k <= 10), ("11 to 20", lambda k: 11 <= k <= 20),
         ("Over 20", lambda k: k > 20)]
rows = []
for label, pred in bands:
    n = sum(v for k, v in sav.items() if pred(k))
    rows.append(f"{label} & {count(n)} & {pct(n / K2['slimmable'])} & {pct(n / (K2['improved'] + K2['tied']))} \\\\")
write("tab_savings.tex", "\n".join([
    r"\begin{tabular}{lrrr}", r"\toprule",
    r"Saving (SinewSlim's cost plus 1, less the sum) & Methods & of what SinewSlim slims & of plans using injection \\", r"\midrule",
    *rows, r"\midrule",
    f"Plans using injection & {count(K2['improved'] + K2['tied'])} & {pct((K2['improved'] + K2['tied']) / K2['slimmable'])} & \\\\",
    f"Extraction alone chosen & {count(K2['slimmable'] - K2['improved'] - K2['tied'])} & {pct((K2['slimmable'] - K2['improved'] - K2['tied']) / K2['slimmable'])} & \\\\",
    r"\bottomrule", r"\end{tabular}", ""]))
IS = P["improved_strict_over_slimmable"]
define("nImprovedStrict", count(IS["count"]))
define("pooledImprovedStrict", pct(IS["pooled"]))
define("popImprovedStrict", pct(IS["population"]))
define("loImprovedStrict", pctn(IS["population_interval"][0]))
define("hiImprovedStrict", pctn(IS["population_interval"][1]))
define("ciImprovedStrict", ci(IS["population"], IS["population_interval"]))
define("medianImprovedStrict", pct(IS["per_repository"]["median"]))
IC = P["improved_composition"]
define("improvedFunctionsOnly", count(IC["functions_only"]))
define("improvedWithPieces", count(IC["with_pieces"]))
define("improvedWithPiecesShare", pct(IC["with_pieces"] / (IC["functions_only"] + IC["with_pieces"])))
CC = P["category3c_composition"]
define("catThreeCFunctionsOnly", count(CC["functions_only"]))
define("catThreeCWithPieces", count(CC["with_pieces"]))
define("catThreeCWithPiecesShare", pct(CC["with_pieces"] / (CC["functions_only"] + CC["with_pieces"])))

# --- concentration (post hoc) and per-repository -------------------------------------------------
SC = P["stuck_concentration"]
define("topTenShare", pct(SC["top10_share"]))
define("topThirtyShare", pct(SC["top30_share"]))
top = SC["top"][0]
define("topRepo", repo(top["repository"]))
define("topRepoStuck", count(top["stuck"]))
define("topRepoStuckShare", pct(top["stuck"] / SC["S1"]))
define("topRepoCatThreeC", count(top["category3c"]))
define("topRepoCatThreeCShare", pct(top["category3c"] / top["stuck"]))
define("topTenCatThreeCMin", pct(min(p["category3c"] / p["stuck"] for p in SC["top"])))
define("topTenCatThreeCMax", pct(max(p["category3c"] / p["stuck"] for p in SC["top"])))
define("reposNoLong", count(SC["repositories_without_long"]))
define("reposNoStuck", count(SC["repositories_without_stuck"]))
define("reposStuckNoCatThree", count(SC["repositories_with_stuck_without_category3c"]))
define("medianLongPerRepo", dec(SC["median_long_per_repository"], 1))
define("medianStuckPerRepo", count(SC["median_stuck_per_repository"]))
CQ = P["category3c_per_repository"]
define("catThreeCQone", pct(CQ["quartiles"][0]))
define("catThreeCQthree", pct(CQ["quartiles"][2]))
define("reposStuckNoCatThreeShare", pct(CQ["without_category3c"] / CQ["repositories"]))
MW = P["category4_machine_written"]
define("machineLines", count(MW["long_table_lines"]))
define("catFourGui", count(MW["gui_builder"]))
define("catFourLongTable", count(MW["long_table"]))
define("catFourMachine", count(MW["either"]))
define("catFourMachineShare", pct(MW["either"] / MW["category4"]))
rows = []
for p in SC["top"]:
    rows.append(f"\\texttt{{{repo(p['repository'])}}} & {TIER_NAME[p['tier']]} & {count(p['long'])} & {count(p['stuck'])} & "
                f"{pct(p['stuck'] / SC['S1'])} & {count(p['category3c'])} & {pct(p['category3c'] / p['stuck'])} \\\\")
write("tab_concentration.tex", "\n".join([
    r"\begin{tabular}{llrrrrr}", r"\toprule",
    r"Repository & Tier & Long & Stuck & of S1 & Category 3 (combined) & of its stuck \\", r"\midrule",
    *rows, r"\bottomrule", r"\end{tabular}", ""]))

# --- post hoc: test code the scope missed ----------------------------------------------------------
T = P["test_paths"]
define("testDroppedLong", count(T["dropped"]["long"]))
define("testDroppedLongShare", pct(T["dropped"]["long"] / POOL["L1"]["long"]))
define("testDroppedStuck", count(T["dropped"]["stuck"]))
define("testDroppedCatThreeC", count(T["dropped"]["category3c"]))
define("testDroppedCatThreeCShare", pct(T["dropped"]["category3c"] / T["dropped"]["stuck"]))
define("testRepos", count(T["repositories_affected"]))
define("testTopSegment", T["segments"][0][0].replace("_", r"\_"))
define("testTopSegmentCount", count(T["segments"][0][1]))
define("testSecondSegment", T["segments"][1][0].replace("_", r"\_"))
define("testSecondSegmentCount", count(T["segments"][1][1]))
TH = T["headline"]
rows = []
for key, name, label in FIG:
    f, g = H[key], TH[key]
    rows.append(f"{label} & {pct(f['population'])} {interval(f['population_interval'])} & {pct(g['population'])} {interval(g['population_interval'])} & "
                f"{count(g['count'])} / {count(g['of'])} \\\\")
write("tab_posthoc_test.tex", "\n".join([
    r"\begin{tabular}{>{\raggedright\arraybackslash}p{6.2cm}llr}", r"\toprule",
    r"Figure & Registered (95\% CI) & Test paths left out (95\% CI) & Count / of \\", r"\midrule",
    *rows, r"\bottomrule", r"\end{tabular}", ""]))
define("testHOnePop", pct(TH["category3c_over_S1"]["population"]))
define("testHOneLo", pctn(TH["category3c_over_S1"]["population_interval"][0]))
define("testHOneHi", pctn(TH["category3c_over_S1"]["population_interval"][1]))
define("testHOneReading", TH["H1"]["reading"])
define("testHTwoPop", pct(TH["improved_over_slimmable"]["population"]))
define("testHTwoLo", pctn(TH["improved_over_slimmable"]["population_interval"][0]))
define("testHTwoHi", pctn(TH["improved_over_slimmable"]["population_interval"][1]))
define("testHOneCi", ci(TH["category3c_over_S1"]["population"], TH["category3c_over_S1"]["population_interval"]))
define("testHTwoCi", ci(TH["improved_over_slimmable"]["population"], TH["improved_over_slimmable"]["population_interval"]))

# --- post hoc: the rescue read against what nothing conventional fixes ---------------------------------
PB = P["plans_by_category"]
for k, name in (("1", "One"), ("2", "Two"), ("3", "Three"), ("4", "Four")):
    define(f"planInCat{name}", count(PB[k]["combined_has_plan"]))
    define(f"planInCat{name}Share", pct(PB[k]["share"]))
NC = P["category3c_over_not_conventional"]
define("nNotConventional", count(NC["of"]))
define("rescueOfNotConventional", pct(NC["pooled"]))
define("rescueOfNotConventionalPop", pct(NC["population"]))
define("rescueOfNotConventionalLo", pctn(NC["population_interval"][0]))
define("rescueOfNotConventionalHi", pctn(NC["population_interval"][1]))
define("rescueOfNotConventionalMedian", pct(NC["per_repository"]["median"]))
define("rescueOfNotConventionalCi", ci(NC["population"], NC["population_interval"]))
define("nCatThreeLost", count(len(P["category3_without_combined_plan"])))
define("nCatThreeLostJumps", count(sum(1 for e in P["category3_without_combined_plan"] if e["combined_reason"] == "jumps")))

# --- post hoc: the shape of the chosen plans -----------------------------------------------------------
SH = P["plan_shapes"]
SHAPES = [("sequence", "Sequence"), ("sequence with early returns", "SequenceReturns"),
          ("branching", "Branching"), ("branching with early returns", "BranchingReturns")]
rows = []
for group, name, label in (("improved", "Improved", "Improved (injection chosen and cheaper)"),
                           ("tied", "Tied", "Tied (chosen by the tie-break)"),
                           ("rescued", "Rescued", "Rescued (category 3, combined split)")):
    n = sum(SH[group].values())
    define(f"shapeN{name}", count(n))
    cells = []
    for key, sname in SHAPES:
        v = SH[group].get(key, 0)
        define(f"shape{name}{sname}", pct(v / n))
        cells.append(f"{count(v)} ({pct(v / n)})")
    seq = SH[group].get("sequence", 0) + SH[group].get("sequence with early returns", 0)
    define(f"shape{name}AnySequence", pct(seq / n))
    define(f"shape{name}AnyBranching", pct(1 - seq / n))
    rows.append(f"{label} & {count(n)} & " + " & ".join(cells) + " \\\\")
write("tab_shapes.tex", "\n".join([
    r"\begin{tabular}{>{\raggedright\arraybackslash}p{5.2cm}rrrrr}", r"\toprule",
    r"Plans & Count & Sequence & Sequence, early returns & Branching & Branching, early returns \\", r"\midrule",
    *rows, r"\bottomrule", r"\end{tabular}", ""]))

br = SH["rescued"].get("branching", 0) + SH["rescued"].get("branching with early returns", 0)
define("shapeRescuedReturnsOfBranching", pct(SH["rescued"].get("branching with early returns", 0) / br))

# --- post hoc: the population a sequence of functions is the way to split --------------------------------
SP = P["sequence_population"]
for key, name in (("sequence_way_over_long", "SeqWay"), ("sequence_way_strict_over_long", "SeqWayStrict"),
                  ("sequence_way_with_tied_over_long", "SeqWayTied"), ("injection_way_over_long", "InjWay"),
                  ("sequence_improved_over_long", "SeqImproved"), ("sequence_rescued_over_long", "SeqRescued"),
                  ("sequence_way_over_methods", "SeqWayMethods")):
    f = SP[key]
    define(f"n{name}", count(f["count"]))
    define(f"pop{name}", pct(f["population"]))
    define(f"ci{name}", ci(f["population"], f["population_interval"]))

# --- post hoc: the construction exceptions, the readings, the parse failures, the run -----------------
E = P["construction_exceptions"]
define("nExceptions", count(len(E)))
define("nExceptionsJumps", count(sum(1 for e in E if e["combined_reason"] == "jumps")))
define("nExceptionsLongStatement", count(sum(1 for e in E if e["combined_reason"] == "long_statement")))
define("exceptionsShare", f"{100 * len(E) / slims:.3f}\\%")
R = P["readings_of_long_methods"]
define("longConventional", count(R.get("conventional", 0)))
define("longEntryPoint", count(R.get("framework_entry_point", 0)))
define("longOfficeFloor", count(R.get("officefloor_function", 0)))
define("allOfficeFloor", count(POOL["R1"].get("officefloor_function", 0)))
define("allEntryPoint", count(POOL["R1"].get("framework_entry_point", 0)))
OF = P["officefloor_reading"]
define("ofTopRepo", repo(OF["repositories"][0][0]))
define("ofTopRepoCount", count(OF["repositories"][0][1]))
define("ofTopEvidence", OF["evidence"][0][0].replace("_", r"\_"))
U = P["unparsed_by_repository"]
define("unparsedTopRepo", repo(U[0][0]))
define("unparsedTopRepoCount", count(U[0][1]))
define("unparsedSecondRepo", repo(U[1][0]))
define("unparsedSecondRepoCount", count(U[1][1]))
ST = P["scan_time"]
define("scanTotalMinutes", minutes(ST["total_seconds"]))
define("scanMedianSeconds", dec(ST["median_seconds"], 1))
define("scanLongestRepo", repo(ST["longest"][0][1]))
define("scanLongestMinutes", minutes(ST["longest"][0][0]))
t0 = datetime.fromisoformat(ST["first_finished_utc"].replace("Z", "+00:00"))
t1 = datetime.fromisoformat(ST["last_finished_utc"].replace("Z", "+00:00"))
wall = (t1 - t0).total_seconds()
define("scanWallHours", f"{int(wall // 3600)}~h~{int(round((wall % 3600) / 60))}~min")
define("scanDate", t0.strftime("%-d %B %Y"))
LM = P["longest_methods"][0]
define("longestMethodLines", count(LM["length"]))
define("longestMethodRepo", repo(LM["repository"]))
define("longestMethodName", LM["method"].split(".")[-1].replace("_", r"\_"))


# --- the plan's own constants (long_method_slim_study/pins.py) and what the plan records as seen -------
sys.path.insert(0, ROOT)
from long_method_slim_study import pins  # noqa: E402

define("planSeed", str(pins.SEED))
define("planTarget", count(pins.TARGET))
define("planAsOf", datetime.strptime(pins.AS_OF, "%Y-%m-%d").strftime("%-d %B %Y"))
define("planMinFunctions", count(pins.MIN_FUNCTIONS))
define("planMinFiles", count(pins.MIN_FILES_WITH_FUNCTIONS))
define("samplerVersion", pins.SAMPLER_VERSION)
define("slimVersion", pins.OFFICEFLOORSLIM_VERSION)
define("slimSha", pins.OFFICEFLOORSLIM_JAR_SHA256[:12])
define("planHOneShare", pct(pins.H1_SHARE, 0))
define("planHOneMinimum", count(pins.H1_MINIMUM))
define("planResamples", count(pins.BOOTSTRAP_RESAMPLES))
define("planLevel", pct(pins.INTERVAL, 0))
# Recorded in docs/ANALYSIS_PLAN.md, section 2 (what was known when the plan was written): the combined
# split on OfficeFloor's own repository, read before the hypotheses were written. Typed here, from the
# plan, as the one place the paper takes them from.
PRIOR = {"stuck": 119, "category3": 12, "slimmed": 327, "improved": 95, "tied": 59}
define("priorStuck", count(PRIOR["stuck"]))
define("priorCatThree", count(PRIOR["category3"]))
define("priorCatThreeShare", pct(PRIOR["category3"] / PRIOR["stuck"]))
define("priorSlimmed", count(PRIOR["slimmed"]))
define("priorImproved", count(PRIOR["improved"]))
define("priorImprovedShare", pct(PRIOR["improved"] / PRIOR["slimmed"], 0))
define("priorTied", count(PRIOR["tied"]))
# Recorded in the plan's amendments and step 3's commit: the scans compared field for field across versions.
# Amendment 3 also scanned 15 of the repositories 0.5.0 had not reached by both 0.5.0 and 0.5.2; the rest were
# never scanned by 0.5.0 and rest on the tests the amendments record.
AMEND = {"scans_0_3_0": 69, "scans_0_5_0": 469, "differing_0_5_1": 2, "rescanned_0_5_1": 150, "spot_0_5_0": 15}
define("amendScansThree", count(AMEND["scans_0_3_0"]))
define("amendScansFive", count(AMEND["scans_0_5_0"]))
define("amendDiffering", count(AMEND["differing_0_5_1"]))
define("amendRescanned", count(AMEND["rescanned_0_5_1"]))
define("amendSpot", count(AMEND["spot_0_5_0"]))
define("amendUncompared", count(S["usable"] - AMEND["scans_0_5_0"] - AMEND["spot_0_5_0"]))

# ---------------------------------------------------------------------------------------------
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "numbers.tex"), "w") as f:
    f.write("% Written by paper/scripts/numbers.py from results/analysis/analysis.json and posthoc.json. Do not edit.\n")
    for k, v in macros.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(f"wrote {len(macros)} macros and {len([n for n in os.listdir(OUT) if n.startswith('tab_')])} tables to {OUT}")
