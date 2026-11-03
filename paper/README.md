# The paper

*What extraction cannot slim, and whether function injection can. A pre-registered count of the long
methods in 580 open-source Java repositories, as they stood before AI coding assistants.*

## What is here

| File | Purpose |
|---|---|
| `main.tex` | The paper. Self contained: no `.bib`, the bibliography is a `thebibliography` environment. Every number is a macro from `generated/numbers.tex`, every table an `\input` of `generated/tab_*.tex`. It names no code, commit, file or command; those are in `anc-README.md`. |
| `generated/` | The number macros and the tables, written by `scripts/numbers.py` from `../results/analysis/analysis.json` (the registered analysis) and `../results/analysis/posthoc.json` (the post hoc readings). **Tracked**, so the paper builds on a fresh clone with no results. |
| `scripts/numbers.py` | The one script behind every number and table; its docstring says what it reads. The plan's own constants come through it too (from `pins.py`), so `main.tex` holds no typed number. |
| `anc-README.md` | The ancillary README packed into the arXiv bundle as `anc/README.md`: the key to every repository, release, file and command. |
| `build.sh` | `pdflatex` twice, `abstract.txt` (git-ignored) and `arxiv.tar.gz` (git-ignored) with the ancillary data under `anc/`. |

## Build

    ../step5_paper.sh     # from the repository root: posthoc.json, generated/, then this build
    ./build.sh            # main.pdf, abstract.txt, arxiv.tar.gz (needs only main.tex and generated/)

## Publishing

arXiv primary class `cs.SE`. Reserve the Zenodo DOI and define `\thedoi` in `main.tex` before
submitting; `build.sh` prints the abstract's character count against arXiv's limit. The Method
section names the registration commit (`\regCommit`), which a reader checks in the public repository.
