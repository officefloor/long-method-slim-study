#!/usr/bin/env bash
#
# Build the paper.
#
#   ./build.sh
#
# The build needs only main.tex and generated/, both tracked, so a fresh clone builds without the
# results or any Python. Regenerating generated/ from the results is
# `../.venv/bin/python scripts/numbers.py` (step 5), not part of the build.
#
# Writes: main.pdf, abstract.txt (the abstract as plain text, for the arXiv and Zenodo forms, with a
# warning past arXiv's 1920 characters) and arxiv.tar.gz, the submission bundle: main.tex and
# generated/ at the root and, under anc/, the data the paper rests on (see pack() and anc-README.md).
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"

abstract() {
  local out=abstract.txt
  sed -n '/^\\begin{abstract}$/,/^\\end{abstract}$/p' main.tex \
    | sed -e '1d' -e '$d' \
    | sed -E -e 's/\\noindent//g' \
             -e 's/\\(emph|textbf|textit|texttt|textsc)\{([^}]*)\}/\2/g' \
    > "$out.tmp"
  python3 - "$out.tmp" "$out" <<'PY'
import re, sys
src, dst = sys.argv[1], sys.argv[2]
macros = dict(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}', open('generated/numbers.tex').read()))
text = open(src).read()
text = re.sub(r'\\([A-Za-z]+)\{\}', lambda m: macros.get(m.group(1), m.group(0)), text)
text = re.sub(r'\\([A-Za-z]+)', lambda m: macros.get(m.group(1), m.group(0)), text)
text = text.replace('{,}', ',').replace('``', '"').replace("''", '"').replace('~', ' ')
text = re.sub(r'\\([%$&_#])', r'\1', text)
text = text.replace('\\', '')
paras, cur = [], []
for line in text.splitlines():
    if line.strip():
        cur.append(line.strip())
    elif cur:
        paras.append(' '.join(cur)); cur = []
if cur:
    paras.append(' '.join(cur))
open(dst, 'w').write('\n\n'.join(paras) + '\n')
PY
  rm -f "$out.tmp"
  local chars; chars=$(wc -c < "$out" | tr -d ' ')
  echo "Wrote $out ($(wc -w < "$out" | tr -d ' ') words, $chars characters, arXiv limit 1920)"
  [ "$chars" -le 1920 ] || echo "WARNING: the abstract is $((chars - 1920)) characters over arXiv's 1920 limit." >&2
}

pack() {
  local stage; stage="$(mktemp -d)"
  trap 'rm -rf "$stage"' RETURN
  mkdir -p "$stage/anc"
  cp anc-README.md "$stage/anc/README.md"
  cp "$ROOT/docs/ANALYSIS_PLAN.md" "$stage/anc/"
  cp "$ROOT/long_method_slim_study/pins.py" "$stage/anc/"
  local d="$stage/anc/analysis"; mkdir -p "$d"
  cp "$ROOT"/results/analysis/analysis.json "$ROOT"/results/analysis/posthoc.json "$d/" 2>/dev/null || echo "   ! results/analysis/*.json missing: run ./step4_analyse.sh and ./step5_paper.sh" >&2
  cp "$ROOT"/results/run-log.jsonl "$d/" 2>/dev/null || echo "   ! results/run-log.jsonl missing" >&2
  d="$stage/anc/exploratory"; mkdir -p "$d"
  cp "$ROOT"/exploratory/results/explore.json "$ROOT"/exploratory/results/tables.md "$ROOT"/exploratory/FINDINGS.md "$d/" 2>/dev/null || echo "   ! exploratory/ results missing: run ./step6_explore.sh" >&2
  d="$stage/anc/sample"; mkdir -p "$d"
  cp "$ROOT"/sample/*.csv "$ROOT"/sample/*.json "$d/" 2>/dev/null || echo "   ! sample/ missing: run ./step2_sample.sh" >&2
  tar czf arxiv.tar.gz main.tex generated -C "$stage" anc
  echo "Packed arxiv.tar.gz ($(tar tzf arxiv.tar.gz | grep -c .) entries, $(du -h arxiv.tar.gz | cut -f1))"
}

abstract
if ! command -v pdflatex >/dev/null 2>&1; then
  echo "pdflatex not found: install TeX Live. main.tex targets pdflatex, which arXiv runs." >&2
  exit 1
fi
pdflatex -interaction=nonstopmode -halt-on-error main.tex > build.log 2>&1 || { grep -n "^!" -A 3 build.log | head -40; exit 1; }
pdflatex -interaction=nonstopmode -halt-on-error main.tex > build.log 2>&1 || { grep -n "^!" -A 3 build.log | head -40; exit 1; }
echo "Built main.pdf ($(pdfinfo main.pdf 2>/dev/null | awk '/Pages/{print $2}') pages); $(grep -c Overfull build.log || true) overfull boxes, $(grep -c 'LaTeX Warning' build.log || true) LaTeX warnings (see build.log)"
grep -n "undefined\|Undefined\|multiply" build.log | head -20 || true
pack
