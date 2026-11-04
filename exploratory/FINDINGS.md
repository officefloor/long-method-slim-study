# Exploratory findings: the category 4 methods

**Exploratory, not registered.** Nothing here changes a registered hypothesis, figure or reading of the
study. It looks at the methods the study left stuck, to choose the next hypotheses. Every number comes
from `results/tables.md` and `results/explore.json`, which `./step6_explore.sh` generates.

**What category 4 is.** A long method (over the 25-line cap) that SinewSlim cannot slim and the combined
split (OfficeFloorSlim) has no plan for. There are **9,059** such methods in **329** of the 580
repositories, 5.4% of long methods (population-weighted, 4.2% to 7.1%).

**Re-reading check.** The harness re-read 9,057 of the 9,059 from source. At the scan's limit of 5,
none has a combined plan, so the harness reproduces the scan.

## 1. Evenly spread, or a few systems?

Both. The methods are widespread: 329 repositories hold at least one. They are also clustered beyond
what repository size explains:

- **The dispersion index is 7.8.** A value of 1 would mean the methods are spread as the long methods are.
- **The 32 "hot" repositories,** whose category 4 rate is significantly above the pooled rate, hold
  **40.4%** of category 4 but only 21.7% of the long methods.
- **The top 10 repositories hold 39.0%,** close to the 38.3% their size alone predicts. Most of the
  clustering is therefore in a middle tier of repositories, not only the largest few.
  `corretto/corretto-8` alone holds 1,170 methods (12.9%).

**By domain** (keyword-coded, crude), the rate is highest in:

| Domain | Rate (interval) |
|---|---|
| games and graphics | 10.2% (3.1–18.0%) |
| numeric, scientific and ML | 8.8% (5.7–12.7%) |
| language tooling | 7.9% (6.3–10.0%) |

It is lowest in:

| Domain | Rate (interval) |
|---|---|
| distributed systems and middleware | 2.9% (2.3–4.7%) |
| learning and examples | 0.9% (0.3–1.8%) |

The mix of causes differs by domain:
- **Numeric and ML code** is mostly data coupling (61.8%).
- **Language tooling** is mostly indivisible (57.1%): switches over tokens and opcodes, and tables.

**The classes split by how they are spread.**

| Pattern | Classes | Top 10 repositories' share (size predicts) | Dispersion |
|---|---|---|---|
| **Concentrated:** a few systems written that way | array initializers | 87.0% (18.2%) | 11.5 |
| | long argument lists | 64.6% (12.8%) | 9.9 |
| | string concatenation | 64.2% (19.5%) | 11.4 |
| | nested try | 87.6% (23.9%) | — |
| | other expressions | 84.8% (20.4%) | — |
| **Spread evenly:** a general habit | flat switches | — | 1.8 |
| | ifs that pass values on | — | 1.0 |
| | the data-limit classes | — | 1.1–1.5 |
| | jumps in loops | — | 0.9–1.5 |

The concentrated classes look like generated code, or a house style of building data in code. The
evenly spread ones look like ordinary ways people write code.

## 2. Your hypotheses, class by class

The three root causes. These are the instrument's reasons, except that control methods whose
reported "jump" crosses no cut are moved to indivisible (see section 5):

| Root cause | Methods | Share | Repositories |
|---|---:|---:|---:|
| Indivisible: one statement over the cap that nothing inside can move | 4,579 | 50.5% | 280 |
| Data: every cut needs too many values | 3,237 | 35.7% | 226 |
| Control: a return, break or continue crosses every cut | 1,243 | 13.7% | 158 |

### Switch: "the number of options is what it is". Supported.

There are 1,528 switches (16.9% of category 4):

| Kind | Methods |
|---|---|
| Short cases (each case under the cap, too many together) | 1,028 |
| Flat tables (every case 3 lines or fewer) | 346 |
| A case over the cap | 154 |

So **1,374 (15.2%)** are long only because of how many options they have.

Their cognitive complexity per line is low: 0.12 for flat tables and 0.21 for short cases, against
0.35 for category 4 as a whole. The length matches the option set, not the logic.

Only the 154 with a case over the cap have a real body to split. They are 90% junctions within
budget (they hand on to other code).

### If: branchy leaf, or passes values on and controls flow? Mostly the second.

There are 750 ifs (8.3%):

| Kind | Methods |
|---|---|
| Else-if chains (dispatch) | 375 |
| **Pass values on** | 170 |
| **Pass values on and jump** | 97 |
| Jump out | 33 |
| **Branchy leaf** (no values out, no jumps) | 75 |

Branchy leaves are the rarest kind (0.8%).

Excluding the dispatch chains, **300 of 375 (80%)** pass values on, jump, or both. These are the long,
dense ones (median length 141 to 186 lines, cognitive per line 0.53 to 0.59).

Even the "leaf" ifs are 75% junctions at the statement level. They don't pass values out, but they do
call into other internal code. So "leaf" in the data sense is not leaf in the call sense, and the
research question becomes: which of an if's outputs (values, jumps, calls) block the split.

### Try or loop: the second reason. Jumps, almost always.

There are 245 nested try, loop or synchronized blocks that are themselves over the cap. Their inner
body is indivisible.

**Nested try:**
- Very flat (cognitive per line 0.08) and 88% junction.
- Typically a try wrapping a long run of calls.
- 87.6% of them are in 10 repositories.

**The control group (1,243, 13.7%) gives the second reason for loops and tries:** the inner body
cannot be separated because a jump crosses every cut inside it. Either the jump leaves the statement,
or it is *nested*: it targets a loop or switch inside the statement, so it leaves no statement but
still crosses a cut between that inner loop's or switch's own statements (for example, a switch's
`break`s inside a loop).

| Where the jump is | Leaves the statement | Nested | Methods |
|---|---:|---:|---:|
| In a loop | 732 (break/continue 377, return 199, both 156) | 102 | 834 |
| In a try | 171 | 26 | 197 |
| In a switch | 97 | — | 97 |
| At the method's top level | 55 | 23 | 81 (with 3 where no jump is found) |
| In a synchronized block, an if or a plain block | 24 | 10 | 34 |

### Data coupling: raise the limit of 5. A steady but diminishing gain.

Share of all 9,059 category 4 methods with a combined plan:

| Limit | Combined plan | Gain from the previous limit |
|---:|---:|---:|
| 5 | 0 | — |
| 6 | 398 (4.4%) | +398 |
| 7 | 691 (7.6%) | +293 |
| 8 | 890 (9.8%) | +199 |
| 10 | 1,134 (12.5%) | +244 over two steps |

The step from 5 to 6 is the largest single gain.

**Within the data group (3,237):**

| Outcome | Methods |
|---|---|
| A plan at some limit up to 10 | 1,134 (35%) |
| Only the blocking statement slims, as a body, by 10; the method as a whole still has no plan | 1,059 (33%) |
| No plan even at 10 (the largest class) | 1,044 (32%) |

The methods with no plan at 10 are the most complex of the data classes: cognitive per line 0.45,
median length 95. They need a different split, not a looser limit.

### Control coupling: "wrapped in something injection can't split". Supported.

**1,128 of the 1,243 (91%)** have the blocking statement inside a loop, try or switch. Injection
splits a sequence of steps, so a step whose body breaks out of its enclosing loop, or returns from the
method, cannot become an injected function. The remaining 55 that return at the top level are long,
branching methods (median 134 lines, cognitive 48) with early returns.

These are the densest classes in the study: cognitive per line 0.58 to 0.63 in loops.

## 3. Complexity and coupling divergence

**Complexity, length-matched.** Each group is standardised to category 4's length distribution:

| Group | Cognitive | cc | Cognitive per line |
|---|---:|---:|---:|
| slimmable | 35.4 | 19.1 | 0.34 |
| category 4 | 46.2 | 26.7 | 0.35 |
| category 3 | 45.9 | 30.7 | 0.33 |
| categories 1–2 (rescued by injection) | **59.6** | 31.6 | **0.47** |

At the same length, category 4 is no more complex than category 3 and less complex than the methods
injection rescues. **Being stuck is about shape, not complexity.** Category 4 holds two different
families:

- **Tables and literals, about 3,400 methods (37%):**
  - array initializers, argument lists, builder chains and string concatenation (cognitive 0);
  - short-case and flat switches;
  - nested try;
  - constructors that only delegate to `super(…)` or `this(…)` (81), and bodies of a single return
    or expression (121), both with cognitive 0.

  These are long without being complex. Arguably they are not long-method smells at all.
- **Dense logic:**
  - jumps in loops and tries;
  - ifs that pass values on;
  - data with no plan at 10.

  Cognitive per line 0.45 to 0.63. This is where splitting would help a reader.

**Coupling divergence, method level.** It does not separate category 4. At matched length and within
budget, category 4 is 77.8% junction, against 76.9% to 84.7% for the other groups. If anything,
category 4 has slightly more catchments (20.3%, against 13.3% for slimmable).

**Coupling divergence, statement level** (the blocking statement taken as a method of its own). It
separates the two families cleanly:

| Family | Classes | Catchment (leaf) | Junction |
|---|---|---:|---:|
| Literals | array initializer, other expressions, string concatenation | 80%, 68%, 62% | — |
| Logic | switch case over the cap, nested try, control in a try | — | 90%, 83%, 79% |

The literal statements take data in and call nothing internal. The logic statements hand on to other
internal code, so there are hand-off points to split at. They are blocked by jumps and carried values,
not by a lack of seams.

**Budget caveat.** Two repositories ran out of their hour of call resolution: `apache/hive` (84.6% of
calls never attempted) and `OpenLiberty/open-liberty` (53.7%). Their internal calls are undercounted, so
they lean towards catchment. The figures above are the within-budget ones (`tables.md`, "Without the
repositories that ran out of budget"). The complexity figures do not depend on call resolution.

## 4. Proposed next hypotheses

1. **Tables are not long methods.** A length cap that ignores data and table statements (literals,
   argument lists, builder chains, flat switches) removes about a third of category 4, and removes
   the most concentrated part. Measure: cognitive per line below about 0.2 identifies them.
2. **The parameter limit of 6.** Raising the limit from 5 to 6 rescues 4.4% of category 4. Test the
   same change on the whole registered population, as a pre-registered parameter study, since it also
   moves categories 1–3.
3. **Jumps as flow outcomes.** A loop or try body whose jumps become the injected function's outcomes
   (continue, break, return as named exits wired in configuration) unblocks the 1,128 control methods
   whose jump is inside a loop, try or switch. This is a tooling change to OfficeFloorSlim, testable on
   these methods.
4. **If outputs.** For an if that passes values on, the branches become injected functions with the
   value as the flow's argument. Test on the 267 ifs that pass values on (with or without jumps).
5. **Codebase style.** Category 4 rates differ by repository beyond size: a per-repository random
   effect is needed for any future rate estimate, and the hot cluster (language tooling, numeric and
   ML, games) is the place to sample for case studies.

## 5. What the instrument calls a jump

The first reading classed 1,462 methods as control. Read again with JavaParser (harness result
versions 2 and 3), **219 of them were mislabels**. In each, the instrument reports "jumps" where
nothing can be cut and no jump crosses a cut:

| What they were | Methods | Now |
|---|---:|---|
| A body of a single statement: `return <expression>` (93 of them), a builder chain, or another lone expression. A single return is the statement's own end | 121 | Indivisible: **one-statement body** |
| A constructor whose whole body is `super(…)` or `this(…)` with a long argument list (e.g. oci-java-sdk models, rstudio file types). The call must stay first | 81 | Indivisible: **constructor delegation** |
| Returns that belong to a lambda or anonymous class inside the statement. They end the lambda, not a cut | 17 | Indivisible |

The first reading also showed 290 methods as "no jump found". 161 of them were real control: a jump
aimed at a loop or switch **nested** inside the blocking statement. The first reading counted only jumps
leaving the whole statement, but a nested jump still crosses a cut inside it. Three remain
unexplained.

The net change: control went from 1,462 (16.1%) to **1,243 (13.7%)**, and indivisible from 4,360
(48.1%) to **4,579 (50.5%)**. None of the conclusions changed. Control is now more clearly what the
hypothesis said: 91% of it is a jump inside a loop, try or switch.

## 6. Loose ends

- **Three control methods with no jump** are still unexplained. They are too few to matter, but worth
  reading.
- **Two methods were not re-read** (both timed out in the harness), and one was not joined to the
  measurer.
- **The domain coding is keyword-based.** The intervals for the small domains (games, numeric and ML)
  are wide.
