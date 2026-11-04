# Exploratory: what the category 4 methods are

**Status: exploratory.** Nothing here was registered, and nothing here changes a registered figure,
the hypotheses or their readings (`docs/ANALYSIS_PLAN.md`, `results/analysis/`). It was done after
the paper's analysis (step 5), to look for the **next** hypotheses: what the long methods that no
split can take apart are, and whether they are spread evenly over the sample or belong to the way a
few systems are written.

Category 4 is the combined split's redesign list: a stuck method (SinewSlim cannot slim it with one
return per piece) for which the combined split has no plan either. The study has 9,059 of them in
329 of the 580 repositories.

## What it does

| Step | Module | What |
|---|---|---|
| 1 | `long_method_slim_study/explore/select.py` | The repositories whose scan (`results/scans/`) holds a category 4 method, as the sample's own rows |
| 2 | `long_method_slim_study/explore/clone_hook.py` | The sampler clones each at its pinned commit (`.java` only) and keeps it; the hook checks the commit |
| 3 | `long_method_slim_study/explore/meta.py` | Each usable repository's GitHub description and topics, once, into the snapshot `data/repo-meta.json` |
| 4 | `harness/Explore.java`, driven by `long_method_slim_study/explore/harness.py` | Re-reads every category 4 method from its clone with the pinned jar (OfficeFloorSlim 0.5.2, SinewSlim 0.2.3, JavaParser) |
| 5 | `long_method_slim_study/explore/report.py` | Joins it all: `results/explore.json`, `results/tables.md` |

The root cause of each method (`explore/rootcause.py`) is read from the scan alone: the combined
split's reason names the outer obstacle and its detail what SinewSlim says of that statement as a
function body; the innermost of the two is the cause, in three groups: **indivisible** (one statement
over the cap that nothing inside can move), **data** (every cut needs too many values) and
**control** (a return, break or continue crosses every cut).

The harness refines each one from the source:

- **the limits raised**: SinewSlim's `max_inputs` and the split's carried values, from 5 to 6, 7, 8
  and 10, for SinewSlim alone, the injection split and the combined split (outer limit; the combined
  split's inner SinewSlim search is fixed at its defaults in 0.5.2, so the blocking body is also
  assessed on its own at each limit, an approximation of raising the inner limit). At 5 the harness
  must reproduce the scan, and does: this is its check.
- **the blocking statement's syntax**: a switch's cases (count, lengths, fall-through); an if's
  branches, else-if chain, the values it hands on (SinewSlim's seam) and the jumps leaving it; what
  makes one expression long (a lambda, an anonymous class, an array initializer, a call chain,
  string concatenation, a long argument list); and, for control, which jumps and in what container.
- **for control, every jump** (result versions 2 and 3): the jumps leaving the blocking statement, and also
  those targeting a loop or switch nested inside it (they cross a cut inside it), the jumps that
  belong to a lambda or anonymous class, and the body's shape (top-level statements, the kind of a lone statement, a constructor
  that only delegates to `super(...)` or `this(...)`). A control method with no jump at all is moved
  to indivisible by the report (`report.regroup`): the instrument reports "jumps" for a delegating
  constructor, a body of a single `return <expression>` and returns inside a lambda. A control method read at an older version
  is read again on the next run; the others keep their results.

The domains (`explore/domains.py`) are coded by keyword rules from each repository's name,
description and topics, first match winning. They are crude on purpose: written down, applied by
code and reviewable, not a validated taxonomy. The coding of every repository is in
`results/explore.json` (`domains.coding`).

## Reproduce

After steps 1 to 3 of the study (the venv, `lib/officefloorslim.jar`, `results/scans/`), with a JDK
(javac 17 or later) and the network:

    ./step6_explore.sh                 # uses the committed exploratory/data/repo-meta.json
    ./step6_explore.sh --refresh-meta  # fetches the descriptions and topics again (they change)

Clones, logs and the raw harness output go under `.tmp/explore/` (not in git, several GB); the
clone and harness steps resume where they stopped. `SHARDS=n` sets how many clones run at once
(default 4). Tests: `python -m unittest discover -s tests`.

## Files

| Path | In git | What |
|---|---|---|
| `../step6_explore.sh` | yes | The step, end to end |
| `harness/Explore.java` | yes | The harness (compiled into `harness/classes/`, not in git) |
| `data/repo-meta.json` | yes | The GitHub snapshot the domains were coded from, dated |
| `results/explore.json` | yes | Every figure: classes, limits, concentration, domains, the coding |
| `results/tables.md` | yes | The tables, generated from `explore.json` |
| `FINDINGS.md` | yes | What the tables suggest, and the hypotheses proposed |
