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
on 2 November 2026: 580 usable Java repositories (`sample/`). Nothing has been scanned yet. See [docs/ANALYSIS_PLAN.md](docs/ANALYSIS_PLAN.md).

## Layout

| Path | What it is |
|---|---|
| `docs/ANALYSIS_PLAN.md` | The questions, sample, instruments, measures and analysis, fixed before any repository is read |
| `step1_setup.sh` … `step4_analyse.sh` | Every step, run by hand in order: set up, draw the sample, scan it, analyse |
| `long_method_slim_study/pins.py` | Every value the plan fixes: seed, size, criteria, scope, versions |
| `long_method_slim_study/scan.py` | The hook the sampler calls for each repository: OfficeFloorSlim's scan, kept raw |
| `long_method_slim_study/analyse.py` | The measures and intervals, from the raw scans; it computes no cost |
| `sample/` | The sampler's CSV and derivation (once drawn) |
| `results/` | The raw scans and the analysis (once run) |
| `paper/` | The write-up (to come) |

## Replicating

```bash
./step1_setup.sh     # .venv, the pinned sampler, the released OfficeFloorSlim (sha256-checked), tests
./step2_sample.sh    # the sample, with the plan's seed; commit sample/
./step3_run.sh       # each repository cloned at its commit and scanned; resumable
./step4_analyse.sh   # results/analysis/analysis.json
```

## Licence

[Apache License 2.0](LICENSE).
