# The paper

*What extraction cannot slim, and whether function injection can. A pre-registered study of
580 Java repositories.*

## What is here

| File | Purpose |
|---|---|
| `main.tex` | The paper. Self contained: no `.bib`, the bibliography is a `thebibliography` environment. Every number is a macro from `generated/numbers.tex`, every table an `\input` of `generated/tab_*.tex`. It names no code, commit, file or command; those are in `anc-README.md`. |
| `generated/` | The number macros and the tables, written by `scripts/numbers.py` from `../results/analysis/analysis.json` (the registered analysis), `../results/analysis/posthoc.json` (the post hoc readings), `../exploratory/results/explore.json` (the exploratory step) and `examples/scan.json`. **Tracked**, so the paper builds on a fresh clone with no results. |
| `examples/` | The paper's two worked examples: `src/main/java/example/Examples.java` (`describe`, stuck under extraction; `build`, a pipeline the combined split prices below extraction), read into Figure 1 by line range, with `// EXTRACT name(inputs)`/`// END EXTRACT: returns …`, `// FUNCTION name: declares …`/`// END FUNCTION: passes on …` and `// INJECTION name: declares …`/`// END INJECTION: passes on …` comments marking the cuts the tools report (SinewSlim's pieces, the combined split's functions, and the injection split's own functions where they differ), named as in the paper's equations (comments are not code lines, so they change no count); `scan.json`, their scan by the pinned OfficeFloorSlim release; and `sinewslim-pieces.json`, SinewSlim's pieces with their inputs and outputs, by `scripts/SinewSlimPieces.java` against the SinewSlim classes the jar bundles. `scan.sh` regenerates both, and every cost and piece the paper prints about them comes from them. Change the Java, rerun `scan.sh`, check that the markers still sit on the reported cuts, and check the `firstline`/`lastline` ranges in `main.tex`. |
| `scripts/numbers.py` | The one script behind every number and table; its docstring says what it reads. The plan's own constants come through it too (from `pins.py`), so `main.tex` holds no typed number. |
| `scripts/SinewSlimPieces.java` | Lists SinewSlim's segmentation of each long method of a file as JSON, for the worked examples (run by `examples/scan.sh`). |
| `anc-README.md` | The ancillary README packed into the arXiv bundle as `anc/README.md`: the key to every repository, release, file and command. |
| `build.sh` | `pdflatex` twice, `abstract.txt` (git-ignored) and `arxiv.tar.gz` (git-ignored): `main.tex`, `generated/` and `examples/` at the root, the ancillary data under `anc/`. |

## Build

    ../step5_paper.sh     # from the repository root: posthoc.json, generated/, then this build
    ./build.sh            # main.pdf, abstract.txt, arxiv.tar.gz (needs only main.tex and generated/)

## Publishing

arXiv primary class `cs.SE`. Before submitting, reserve three Zenodo DOIs and define them in
`main.tex`: `\thedoi` (the paper), `\plandoi` (the plan as it stood at the registration commit:
`git show bcb5d48:docs/ANALYSIS_PLAN.md` and `git show bcb5d48:long_method_slim_study/pins.py`,
deposited as they are) and `\scansdoi` (the raw scans, `results/scans/`, about 400 MB, so that a
replication does not depend on the 580 repositories staying on GitHub). Each is printed only where
defined. `build.sh` prints the abstract's character count against arXiv's limit. The Method section
names the registration commit (`\regCommit`), which a reader checks in the public repository.
