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

**Status:** the analysis plan is drafted, not registered. No sample has been drawn and nothing
has been scanned. See [docs/ANALYSIS_PLAN.md](docs/ANALYSIS_PLAN.md).

## Layout

| Path | What it is |
|---|---|
| `docs/ANALYSIS_PLAN.md` | The questions, sample, instruments, measures and analysis, fixed before any repository is read |
| `sample/` | The sampler's CSV and derivation (once drawn) |
| `harness/` | The hook the sampler calls for each repository, and the analysis (to come) |
| `results/` | The raw scans and the analysis (once run) |
| `paper/` | The write-up (to come) |

## Licence

[Apache License 2.0](LICENSE).
