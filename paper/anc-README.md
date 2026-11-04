# Ancillary data for the paper

*What extraction cannot slim, and whether function injection can. A pre-registered study of
580 Java repositories.* Daniel
Sagenschneider, 2026.

This directory holds the data the paper is computed from and the key to every public repository
involved. The raw scans (one JSON per repository, about 400 MB together) are **not** included: the
study's step 3 reproduces them from the pinned sample and the pinned jar below.

## The repositories

Everything is public and Apache-2.0 licensed.

| Repository | What it is |
|---|---|
| https://github.com/officefloor/long-method-slim-study | **The study and the paper.** The registered analysis plan with its amendments (`docs/ANALYSIS_PLAN.md`, registered by commit `bcb5d48` on 1 November 2026), the pinned values (`long_method_slim_study/pins.py`), the numbered step scripts, the scan hook, the analysis, the post hoc readings, the sample, the run log, the analysis output and the paper with its number generator (`paper/`). |
| https://github.com/officefloor/open-source-repository-sampler | **The sampler.** Release 0.3.0 (commit `25c4bf6`, on PyPI); drew the sample with seed `20261101` as of 1 December 2020, from GitHub's index and the plan's criteria alone, and cloned each repository at its pinned commit for the scan. |
| https://github.com/officefloor/OfficeFloorSlim | **The instrument.** Release 0.5.2 (jar sha256 `513b669f…`, pinned in `pins.py`), whose `scan` command reports every long method's SinewSlim assessment, injection split and combined split; its `DESIGN.md` records the cost models and when each question was decided. |
| https://github.com/officefloor/SinewSlim | **The extraction search** OfficeFloorSlim is built on: release 0.2.3 (Maven Central), under its defaults. |
| https://github.com/officefloor/OfficeFloor | **The framework** whose function injection the split projects. |

## What is here

| Path | What it is |
|---|---|
| `ANALYSIS_PLAN.md` | The registered plan, with Amendments 1 to 3. |
| `pins.py` | Every value the plan fixes: seed, size, criteria, as-of date, versions, the jar's digest, the hypothesis bar. |
| `sample/` | The sampler's CSV (757 drawn, 580 usable) and its derivation (the frame, the command, the strata). |
| `analysis/run-log.jsonl` | Step 3's run log: each repository's commit, status, scan time. |
| `analysis/analysis.json` | Step 4, the registered analysis: every measure per repository, per tier and pooled; the headline figures with their intervals; every method where the split's worst seam is larger than SinewSlim's. |
| `analysis/posthoc.json` | Step 5, the post hoc readings: the test-path sensitivity, the combined split's plans within each category and the rescue over what nothing conventional fixes, H2 read against plain extraction (the sum strictly below SinewSlim's cost itself), the quartiles of each repository's own rescue share, the 16 and 189 methods on which the instrument contradicts its own construction, the composition and the shape (sequence or branching) of the rescued and improved plans, the share of long methods a sequence of functions is the way to split (plain and strict), the concentration of the stuck methods, a lower bound on machine-written code among the category 4 methods, the readings, the scan times. |

## Commands

From a clone of the study's repository:

    ./step1_setup.sh      # .venv, the pinned sampler, the released jar (sha256-checked), the tests
    ./step2_sample.sh     # the sample, with the plan's seed (it refuses any other)
    ./step3_run.sh        # every repository cloned at its commit and scanned; about two hours
    ./step4_analyse.sh    # results/analysis/analysis.json
    ./step5_paper.sh      # results/analysis/posthoc.json, paper/generated/, paper/main.pdf
