# long-method-slim-study

What extraction cannot slim, and whether function injection can: the long methods of a random
sample of open-source Java repositories, priced two ways.

- **Extraction**, by [SinewSlim](https://github.com/officefloor/SinewSlim): can each long method
  be brought under 25 code lines by extracting methods, and at what cost?
- **Function injection**, by [OfficeFloorSlim](https://github.com/officefloor/OfficeFloorSlim):
  can it be split into functions that a framework injects and sequences, and at what cost?

The study computes no cost of its own. It draws the sample with
[open-source-repository-sampler](https://github.com/officefloor/open-source-repository-sampler)
and calls the released products' command lines for every figure.

**Status:** the analysis plan was registered on 1 November 2026 (`bcb5d48`). The sample was drawn
on 2 November 2026: 580 usable Java repositories (`sample/`). All 580 were scanned on 3 November 2026
by OfficeFloorSlim 0.5.2 (Amendments 1 to 3) and analysed the same day (`results/analysis/analysis.json`):
**H1 refuted** (the combined split rescues 22.2% of the stuck methods, 95% interval 20.3% to 24.3%,
against the registered quarter); **H2** an estimate, as registered (29.0%, 24.3% to 34.6%). The paper is in
`paper/`. See [docs/ANALYSIS_PLAN.md](docs/ANALYSIS_PLAN.md).

## Layout

| Path | What it is |
|---|---|
| `docs/ANALYSIS_PLAN.md` | The questions, sample, instruments, measures and analysis, fixed before any repository is read |
| `step1_setup.sh` … `step5_paper.sh` | Every step, run by hand in order: set up, draw the sample, scan it, analyse, write up |
| `long_method_slim_study/pins.py` | Every value the plan fixes: seed, size, criteria, scope, versions |
| `long_method_slim_study/scan.py` | The hook the sampler calls for each repository: OfficeFloorSlim's scan, kept raw |
| `long_method_slim_study/analyse.py` | The measures and intervals, from the raw scans; it computes no cost |
| `long_method_slim_study/posthoc.py` | The post hoc readings for the paper (none registered; labelled so): the test-code leak, the exceptions to the construction, H2 against plain extraction, the per-repository quartiles, the composition and shape of the plans |
| `sample/` | The sampler's CSV and derivation (once drawn) |
| `results/` | The run log, the analysis and the post hoc readings; the raw scans (`results/scans/`) are not kept in git, as step 3 reproduces them |
| `paper/` | The paper: `main.tex`, whose every number is a macro written by `paper/scripts/numbers.py` from the committed analysis; `./build.sh` makes `main.pdf` |

## Replicating

```bash
./step1_setup.sh     # .venv, the pinned sampler, the released OfficeFloorSlim (sha256-checked), tests
./step2_sample.sh    # the sample, with the plan's seed; commit sample/
./step3_run.sh       # each repository cloned at its commit and scanned; resumable
./step4_analyse.sh   # results/analysis/analysis.json
./step5_paper.sh     # results/analysis/posthoc.json, paper/generated/, paper/main.pdf
```

## Licence

[Apache License 2.0](LICENSE).
