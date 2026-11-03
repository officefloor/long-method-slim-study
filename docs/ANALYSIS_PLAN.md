# Analysis plan: what extraction cannot slim, and whether function injection can

> **Status: REGISTERED** on 1 November 2026, by commit `bcb5d48` (`pins.REGISTERED` set), with
> every **[DECIDE]** and **[FILL]** settled, before the sample was drawn. Any change since is a
> dated amendment that says what had been seen when it was made.
>
> *2 November 2026: this status line only, which still read "DRAFT, not yet registered" after
> registration. Nothing else in the plan changed. Seen by then: the drawn sample (`sample/`);
> no repository had been scanned.*
>
> *2 November 2026: Amendment 1, the instrument re-pinned from OfficeFloorSlim 0.3.0 to 0.5.0 for
> speed alone (section 9).*
>
> *3 November 2026: Amendment 2, the instrument re-pinned from OfficeFloorSlim 0.5.0 to 0.5.1 for
> speed alone (section 9).*
>
> *3 November 2026: Amendment 3, the instrument re-pinned from OfficeFloorSlim 0.5.1 to 0.5.2:
> 0.5.1 did not give 0.5.0's results on 2 repositories (section 9).*

## 1. Purpose

A method of 26 code lines or more is *long* (Sagenschneider, *What reviewers call a Long Method
is a length*, doi:10.5281/zenodo.23749773). That length was found on code people wrote and
reviewed, so this study reads code people wrote: a random sample of open-source Java
repositories, each as it stood before AI coding assistants were in general use. It asks, of
their long methods:

1. how many there are, and what slimming them by extracting methods costs;
2. how many cannot be slimmed by extraction at all;
3. how many of those a split into functions, which a framework injects and sequences (function
   injection, as OfficeFloor does it), can take apart, and how many only that split can: its
   **reach**;
4. where both can split a method, how the two plans compare in the terms they share: the worst
   seam, the number of parts and the largest part, its **shape**;
5. why the split fails, where it does;
6. what a developer would actually do, functions where the flow divides with extracted methods
   inside them (the **combined split**): how many stuck methods it rescues (**H1**), and how often,
   where extraction alone would do, it chooses injection and costs less (**H2**).

Reach and shape are what this study means by function injection being cheaper than extraction.
The two total costs count different things and are never compared (section 5), except inside
the combined split, which adds them to choose its plan (section 4).

It is descriptive, with one confirmatory hypothesis, H1, and a second question, H2, estimated
without a threshold (section 6, *Hypotheses*); how each is read is fixed here. It reports every figure it computes, whichever way it points.

## 2. What was known when this was written

- **Seen.** SinewSlim's results on other samples: the long-method paper's corpora, among them
  `seed3`, a sample drawn by the same sampler with seed 3, on whose facts SinewSlim's search was
  checked for parity with the study's `split.py`. OfficeFloorSlim's scan of OfficeFloor's own
  repository (category 3, below: 8 of 119 stuck methods under the injection split) and of one
  agent-grown Spring application (0 of 9). The combined split on OfficeFloor's own repository
  only, read while it was built and before its hypotheses were written: category 3, 12 of 119
  stuck methods (10.1%, against H1's quarter); of the 327 long methods SinewSlim slims, injection
  chosen and cheaper for 95 (29%) and chosen on a tie for 59 more. That is one repository, written
  by the author: it is why the expectation below is stated, not a sample of this study's frame.
- **Expectation.** The author expects that, on code written before AI assistants, OfficeFloor has
  a better chance of splitting long methods than conventional extraction (H1 and H2 make that
  testable). The one repository seen points against H1: 10% is well under a quarter. Both are
  stated before the sample is drawn.
- **No categories on `seed3`.** OfficeFloorSlim has never been run on `seed3`, and is not to be
  before this plan is registered.
- **Not seen.** Any repository of this study's sample: it has not been drawn.
- **Conflict of interest.** The author created OfficeFloor, SinewSlim and OfficeFloorSlim. This
  is why the sample is drawn by an independent tool with its seed fixed here, why repositories
  owned by the author are excluded, why every cost is the products' (this study computes none
  of its own), why the two costs are never put in a common unit, and why every case where
  function injection does worse is reported.

## 3. Sample

- **Tool.** `open-source-repository-sampler` **0.3.0** (25c4bf6, from PyPI), which draws a
  seeded, stratified simple random sample of GitHub repositories and pins each to a commit,
  here as of the date below (`--as-of`).
- **As of: 1 December 2020** (decided 1 November 2026). GitHub Copilot's technical preview
  opened on 29 June 2021; 1 June 2021 is before it, and this date is six months before that
  again, so that no code in the sample was written with AI code generation. Every repository
  was created before the date, is pinned to the newest commit on its default branch's
  first-parent history committed before it, and is judged by the criteria there.
- **Frame.** Java repositories created before the as-of date, in three popularity tiers: high
  (over 5,000 stars), mid (1,000 to 5,000) and low (200 to 999).
- **Criteria** (as `seed3`'s): at least 50 functions, in at least 15 files; repositories owned by
  `officefloor` or `sagenschneider` excluded.
- **Size: 580 usable repositories** (decided 1 November 2026), as `seed3`. Before the as-of
  date GitHub lists 546 high-tier, 2,539 mid-tier and 8,818 low-tier Java repositories (1
  November 2026); tiers are drawn equally, so 580 is about 193 usable a tier, well within each,
  while 1,160 would take most of the high tier for intervals only about 30% narrower.
- **Seed: `20261101`** (decided 1 November 2026): a new seed, not 3, so the sample is one
  nobody has looked at. The first sample drawn with it is used.
- **Tiers** are drawn equally, so population estimates weight each stratum by population over
  usable, as the sampler's derivation gives them; between-tier comparisons need no weights.

## 4. Instruments

Every cost comes from the released products. This repository computes none.

- **OfficeFloorSlim 0.5.2** (Amendments 1 to 3; registered as 0.3.0, whose results it gives), its
  command line `officefloorslim scan --format json` (schema `officefloorslim-scan/2`, with the
  combined split's fields added in 0.3.0), run once per repository at its pinned commit. It reports, for every long method, three
  columns:
  - **SinewSlim's assessment**, under SinewSlim's defaults, from the SinewSlim libraries it is
    built on (**SinewSlim 0.2.3**, from Maven Central; 0.2.0 when registered): trigger 26, target 25, at most 5
    parameters and 1 return per piece, records offered, no framework reading;
  - **the OfficeFloor split**, `officefloorslim-split/1`: every line in a function, none over
    25 code lines; its cost the values carried between functions, plus 1 per function and per
    flow; loops and lambda bodies never cut; at most 5 carried values per function. The cost
    model and its limits were decided before this plan (OfficeFloorSlim's `DESIGN.md`, *The
    OfficeFloor split*);
  - **the combined split**, `officefloorslim-split/2` (`DESIGN.md`, *The combined split*,
    questions 8 to 11, decided 1 November 2026 before any figure of it existed): functions cut by
    the same rules, but a function over the target is allowed when SinewSlim's search, under its
    defaults, slims its body as a method of its own, its declared values its parameters; a body
    SinewSlim slims only with a record is refused. The plan is the smallest **sum** of the
    injection total and SinewSlim's cost of the pieces inside the functions, then the fewer
    pieces, then the fewer functions. The method as one function, slimmed by SinewSlim, is always
    a candidate, at SinewSlim's cost plus 1: such a plan is `extraction_only` and counts as
    SinewSlim's, not injection's.
- **Scope: production Java, no tests** (decided 1 November 2026): every `.java`, leaving out
  `src/test`, `src/it`, `build`, `target`, `generated` and `node_modules` (OfficeFloorSlim's
  defaults), and `**/test/**` and `**/tests/**`, since open-source projects do not all follow
  Maven's layout.
- **Growth** is not measured: it needs each repository's history, and the questions do not.
- **What is downloaded:** each repository at its pinned commit, shallow, and only its `.java`,
  `.yml`, `.yaml`, `.woof` and `.officefloor` files (the sampler's `--only`): the files the scan reads.

## 5. Measures

Per repository, and pooled:

| Code | Measure |
|---|---|
| L1 | Methods with a body; long methods (26 code lines or more) |
| L2 | Long methods by SinewSlim status: slimmable, slimmable but locked, slimmable only with a record, not slimmable |
| L3 | SinewSlim's slim cost of each slimmable long method |
| S1 | **Stuck:** long methods SinewSlim cannot slim with one return per piece (`not_slimmable` and `slimmable_with_record`) |
| S2 | Of S1, those the OfficeFloor split has a plan for, whatever else could fix them |
| S3 | Of S1, by category, tested conventional first: 2 if records slim it; else 1 if SinewSlim's defaults slim it once jumps are ignored; else **3** if the OfficeFloor split has a plan; else 4 |
| C1 | Where both have a plan: SinewSlim's worst seam and the split's worst seam, side by side |
| C2 | Where both have a plan: SinewSlim's pieces and the split's functions; the largest of each |
| F1 | The split's reasons where it has no plan: loop, long statement, try, switch, carried values, jumps |
| R1 | Every method by reading: OfficeFloor function, framework entry point, conventional |
| P1 | Per repository with at least one stuck method: its S2 over S1, and its category 3 over S1 (and the same under the combined split) |
| S2c | Of S1, those the combined split has a plan for (it uses injection for every one: a stuck method has no one-function plan) |
| S3c | Of S1, by category with the combined split as the OfficeFloor column: category 3 is **H1**'s count |
| K1 | Every long method under the combined split: a plan using injection, `extraction_only`, or none (with its reason) |
| K2 | Of the long methods SinewSlim slims: those where the combined split chooses injection and its sum is below SinewSlim's cost plus 1 (**improved**, H2's count), equal to it (**tied**, settled by the tie-break), and the distribution of the saving |

**By construction, not findings:** the combined split always has a plan where SinewSlim slims
a method, and its sum is never more than SinewSlim's cost plus 1. Neither is reported as a result.

**Never compared:** SinewSlim's total cost and the split's total cost. They count different
things, and the weight that would turn one into the other is the very thing a sceptical reader
would say was chosen to favour function injection. C1 and C2 compare what both measure.

## 6. Analysis

- **The unit is the repository.** Intervals are a percentile bootstrap over repositories within
  strata: 10,000 resamples, seed `20261101`, 95%.
- **Headline figures:** S2 over S1, and S3's category 3 over S1, each pooled and per tier, with
  intervals; population estimates weighted by stratum.
- **Per repository (P1),** beside the pooled figures: the median of each repository's share,
  over the repositories with at least one stuck method, and how many there are. The pooled
  figures count each stuck method once, so a few very large repositories weigh most; the median
  shows whether they carry the result.
- **Reported in every case:** every figure above, per tier and pooled; F1 in full; every method
  where the split's worst seam is larger than SinewSlim's; the unusable and errored
  repositories, with the sampler's reasons.
- **Unparseable files** are counted and listed, and left out.

### Hypotheses

Each is read from the 95% interval of its **population** estimate (weighted by stratum),
pooled over the sample; the pooled, per-tier and per-repository figures are reported beside it.

- **H1 (rescue).** On code written before AI assistants, the combined split rescues at least a
  quarter of the stuck methods: category 3 under the combined split (S3c) is at least 25% of S1,
  and at least 30 methods (the go/no-go bar, fixed 31 October 2026, before any scan).
  **Supported** if the whole interval is at or above 25% and the count is at least 30;
  **refuted** if the whole interval is below 25%; **inconclusive** otherwise.
- **H2 (improvement).** Where extraction alone would slim a method, the combined split chooses
  injection and costs less: K2's improved over the long methods SinewSlim slims.
  **No threshold (decided 1 November 2026): it is reported as an estimate with its interval.**
  OfficeFloor's own code gave 29% (section 2) before this was set, so a share chosen now would be
  chosen knowing it, and would test nothing. H1, whose quarter was fixed before any scan, is the
  test of the expectation. Ties are never counted as
  improvements: the tie-break favours injection, and the tied count is reported beside H2.

The injection split's figures (S2, S3) are reported beside the combined split's, so a reader
sees how much of the rescue is function injection's own and how much the extracted methods
inside the functions.

## 7. Order of work

Each step is a script, run by hand; the values it uses are in `long_method_slim_study/pins.py`.

1. Settle every **[DECIDE]** and **[FILL]** here and in `pins.py`, set `pins.REGISTERED`, and
   commit both. This is registration. `step1_setup.sh` then fetches the pinned release.
2. `step2_sample.sh`: draw the sample with the fixed seed (it refuses another seed, or an
   unregistered plan), and commit the sampler's CSV and derivation.
3. `step3_run.sh`: the sampler clones each usable repository at its pinned commit and calls
   `officefloorslim scan --no-growth`; the JSON for each is kept, raw.
4. `step4_analyse.sh`: the measures and intervals of sections 5 and 6, then the write-up.

## 8. Threats

- **One language.** Java only: the products read Java.
- **A projection.** The sample's code was not written for function injection, so the split's
  plan is what it *would* cost, not what anyone paid. Its migration cost is reported apart.
- **The split's limits decide much.** Loops and lambda bodies are never cut between functions.
  A different choice would change S2 and S3; the choice was made before this plan, for reasons of
  its own. In the combined split they stay whole inside a function, where SinewSlim may slim them.
- **The combined split's tie-break favours injection.** On a tie on the sum, the fewer pieces
  win, so injection is chosen over the one-function plan. Ties are therefore counted apart from
  improvements (K2), and every plan a tie decided is flagged in the raw scans (`tie_by_pieces`).
- **The injection split charges one flow too many** for an early `return` in a method's last
  function (it goes where the end goes), as released in `officefloorslim-split/1` and left so
  (decided 1 November 2026). It can only overstate the injection split's costs, never flatter it;
  the combined split does not charge it for the method as one function.
- **Adding the two costs.** The combined split adds the injection and extraction totals to choose
  its plan, a weight of 1 to 1: both count values crossing a boundary and 1 per part, but a
  different weight could choose differently. The two parts are reported beside the sum.
- **Stars are attention, not quality.** The tiers span attention; they say nothing of craft.
- **Survivorship.** The frame and the stars are GitHub's today. A repository deleted or made
  private since the as-of date is not in the frame, and a repository's tier is its popularity
  now, not then.
- **Dates and authorship.** The as-of commit is chosen by committer date, which rebased or
  imported history can misstate. Code before the date is not certainly hand-written either:
  generators and templates predate AI assistants, and generated directories are only left out
  where they are named so.
- **The size criterion is counted by Lizard** (1.23.0, as the sampler pins it), which does not
  read Java records: a repository near the criterion that uses them could be undercounted and
  excluded. Records arrived as a final feature in Java 16 (March 2021), after the as-of date
  (only as a preview in Java 14 and 15), so this is close to moot.

## 9. Amendments

### Amendment 1 (2 November 2026): OfficeFloorSlim 0.3.0 → 0.5.0, for speed alone

**What happened.** Step 3 ran 69 repositories with OfficeFloorSlim 0.3.0, then stayed on the 70th,
`intoolswetrust/jsignpdf`, for over three hours. A thread dump showed the combined split
(`officefloorslim-split/2`) slimming candidate function bodies with SinewSlim. jsignpdf holds
three NetBeans-generated `initComponents()` methods of 255, 385 and 575 flat statements. Under
`split/2` every run of statements over the target is a candidate body, about n²/2 runs of a
sequence of n statements, and 0.3.0 slimmed each from scratch: about 160,000 SinewSlim searches
for the largest method. Generated GUI code is common in Java of this period, so the step could
not finish in any reasonable time.

**What changed.** OfficeFloorSlim 0.5.0, on SinewSlim 0.2.1, assesses a sequence's runs together
(SinewSlim's `Assessor.runs`): one walk of SinewSlim's search per first statement serves every
run starting there, since the search's states after a run's statements do not depend on what
follows them. The cost model, the limits, the selection and the scan's fields are unchanged;
0.5.0 adds `links` to each plan (the flows between its functions), which this study does not
read. Nothing in sections 1 to 8 changes but the version.

**Evidence that the results are the same.** Before re-pinning:

- SinewSlim's `RunSlimmerTest`: every run of every sequence of its committed parity subset (1,200
  methods, 141,111 runs, 30,590 slimmable) slimmed and assessed both ways: all equal.
- SinewSlim's full parity on `seed3` (the facts only, as before registration): 187,285 methods,
  936,425 results, 0 mismatched.
- The scans of 0.3.0 and the released 0.5.0 jar compared field for field, all but `links` and the
  scan's run time: OfficeFloor's repository (446 long methods), and jsignpdf's 255- and
  385-statement methods (0.3.0: 7 and 36 minutes; 0.5.0: 10 and 27 seconds). All equal.
  The 575-statement method (`SignPdfForm`), scanned by 0.3.0 from its own jar at low priority:
  3 hours 17 minutes (11,843 s); 0.5.0: 75 seconds. All 6 of the file's long methods equal.

**After step 3**, the 69 repositories 0.3.0 had scanned are compared field for field with their
0.5.0 scans, and the result is reported with the analysis, whichever way it falls; the 0.3.0
scans are kept for this (`results-0.3.0-partial/`, not part of the analysis).

**What had been seen.** The sample (`sample/`). The 69 raw 0.3.0 scans existed but had not been
opened, and are not used. Of jsignpdf, to find the cause: the names and sizes of its three
`initComponents()` methods, from its source, and those methods' scans by each version compared
only for equality, no field of them being read. No figure of section 5 had been computed.

### Amendment 2 (3 November 2026): OfficeFloorSlim 0.5.0 → 0.5.1, for speed alone

**What happened.** Step 3 ran 469 repositories with OfficeFloorSlim 0.5.0 before it was stopped
at the 471st. 463 of them took 0.9 hours of scanning together; six took 8.7 hours: MeteoInfo
(3 h 33 min), MyBookshelf (3 h 12 min), jsignpdf, Android-nRF-Mesh-Library and open-liberty (about
34 min each), and AppManager (17 min). `plantuml/plantuml` failed after 9.2 hours (the scan
exited 1), and `Grover-c13/PokeGOAPI-Java` was 41 minutes in when the step was stopped. The cause
was generated tables: methods of thousands of one-line statements, such as an encoding
detector's frequency table (MyBookshelf's `EncodingDetect.initialize_frequencies()`, about 3,670
statements) or a vendored parser's keyword map (jsignpdf's copy of iText, 1,782). 0.5.0 walked
SinewSlim's search from every statement of such a method to its end, and built the facts of
every one of the n²/2 runs to ask of them.

**What changed.** OfficeFloorSlim 0.5.1, on SinewSlim 0.2.2. Three changes, each exact:

- SinewSlim's search keeps only the ways of handling a run that can still bring it to the
  target (a way's lines left only grow as the search goes on), and a walk stops when none is
  left; a run past that point is known not to slim without its facts being built.
- In a flat method that fits one function, the whole method as one function is taken without
  the search when a lower bound on every other plan's total shows none can match it.
- Each statement's jumps are counted once per sequence, not once per run.

The cost model, the limits, the selection and the scan's fields are unchanged. Nothing in
sections 1 to 8 changes but the versions.

**Evidence that the results are the same.** Before re-pinning:

- SinewSlim's `RunSlimmerTest`: every run of its parity subset (141,111 runs), and the 8,347 the
  walk alone answers "cannot be slimmed" for, each checked against slimming from scratch: all
  equal. SinewSlim's full parity on `seed3`: 187,285 methods, 0 mismatched.
- OfficeFloorSlim's `ShortcutTest`: the shortcut's plan against the search's on 400 random flat
  and nearly flat methods (97 taken by the shortcut): all equal.
- The 150 repositories step 3 had scanned when the change was made, cloned again at their pinned
  commits and scanned by the 0.5.1 build, then compared field for field with their 0.5.0 scans,
  all but the checkout path and the run time: 150 of 150 equal. MeteoInfo took 274 s (0.5.0:
  3 h 33 min), MyBookshelf 271 s (3 h 12 min), jsignpdf 333 s (34 min), each run two at a time
  beside step 3.
- An earlier build differed from 0.5.0 in one field of one method (apache/hive). The cause was in
  0.5.0 itself: it keeps the result of a run by the run's first and last lines, and two different
  runs can share them when two statements share a line (`x = f();;`), so whichever is asked of
  first decides both. The earlier build asked in another order. 0.5.1 keeps 0.5.0's order
  exactly, and the 150 were compared again with the final build. The quirk is left as it is for
  this study, so that the instrument's results do not change; it is to be fixed after.
- The released 0.5.1 jar (built by its release from SinewSlim 0.2.2 on Maven Central; the 150 were
  scanned by a local build of the same commits) compared again on MeteoInfo, MyBookshelf,
  jsignpdf and apache/hive: all four equal to 0.5.0 (179, 180, 187 and 29 seconds).

**Step 3 is run again from the start** on 0.5.1, so every scan comes from one jar. **After step
3**, the 469 repositories 0.5.0 had scanned are compared field for field with their 0.5.1 scans,
and the result is reported with the analysis, whichever way it falls; the 0.5.0 scans and run log
are kept for this (`results-0.5.0-partial/`, not part of the analysis). The comparison Amendment 1
promised, of the 69 0.3.0 scans, is made against the 0.5.1 scans.

**What had been seen.** The sample (`sample/`). Of step 3's run log, each repository's status,
error message and scan time. The 469 raw 0.5.0 scans had not been opened, and are not used:
comparing the 150 with 0.5.1 read only whether each pair was equal and, where not, the path of
the differing field. For the apache/hive difference: the differing field's path
(`combined.tie_by_pieces` of one method), that method's file, signature and line in the 0.5.1
scan, and its source, which was then scanned alone by both versions, compared again only for
equality. Of MyBookshelf and jsignpdf, to find the cause: the sizes of their longest flat
statement runs, from their source. No figure of section 5 had been computed.

### Amendment 3 (3 November 2026): OfficeFloorSlim 0.5.1 → 0.5.2, as 0.5.1 changed two results

**What happened.** Step 3 ran all 580 repositories on 0.5.1 in 1 hour 52 minutes. Amendment 2
promised that its scans be compared field for field with the 469 that 0.5.0 had scanned, and the
69 of 0.3.0. The 69 were all equal; of the 469, 467 were equal and 2 were not:
`corretto/corretto-8` (in one method, `DESCrypt.expandKey`, the combined split's functions) and
`yellowstonegames/SquidLib` (in one method, `IsaacRNG.init`, SinewSlim's obstacle). So 0.5.1 was
not the instrument Amendment 2 said it was, and its scans are not used (`results-0.5.1/`, kept,
not part of the analysis).

**The cause.** SinewSlim 0.2.2 dropped, as its search went, the states that already left more
lines than could reach the target, taking it that the lines a state leaves only grow. They can
fall: statements that share a line (both methods are written several statements to a line,
inside loops and ifs) are each counted against it, so a loop or if slimmed from inside can leave
fewer than no lines. The 150 repositories compared before Amendment 2 happened to have no method
where this changed a result, and no test made such a method.

**What changed.** OfficeFloorSlim 0.5.2, on SinewSlim 0.2.3. A state is now dropped only if, after
allowing for the most the later statements can lower its lines left, it can still reach no end
of its walk. The shortcut that took a flat method whole (Amendment 2's second change) is removed:
it never applied to the slow methods, and its bound had the same weakness. Nothing else in
Amendment 2's changes, or in sections 1 to 8, changes but the versions.

**Evidence that the results are the same.** Before re-pinning:

- SinewSlim's `RunSlimmerSharedLinesTest`, new: methods generated with several statements to a
  line inside loops and ifs, nearly all with a statement leaving fewer than no lines. Every run of
  each (329,264) slimmed by the walks and from scratch, and each method (300) by the pruned and
  the whole search under every variant the assessment uses: all equal. Both checks fail on 0.2.2.
- SinewSlim's `RunSlimmerTest` and the full parity on `seed3` (187,285 methods, 0 mismatched), as
  before.
- The two methods' files, and the apache/hive file of Amendment 2, scanned alone by 0.5.0 and
  0.5.2 (a local build, then the released jar): equal.
- 15 of the 111 repositories 0.5.0 had not scanned, scanned by both 0.5.0 and 0.5.2: all equal.
  `plantuml/plantuml`, which 0.5.0 cannot finish (it failed after 9.2 hours), took 443 seconds
  and equals its 0.5.1 scan.

**After step 3**, its scans are compared field for field with the 469 of 0.5.0
(`results-0.5.0-partial/`), and the 69 of 0.3.0, and the result is reported with the analysis,
whichever way it falls. The other 95 repositories 0.5.0 had not scanned are not compared with
0.5.0 before the analysis: running 0.5.0 on them takes hours, and the tests above are what show
the walks exact. Should the comparison of the 469 find any difference, the analysis waits for
its cause.

**What had been seen.** The sample (`sample/`), and step 3's run logs (status, error and time of
each repository). Of the 0.5.1 scans: whether each of the 538 compared was equal and, for the two
that were not, the paths of the differing fields, and each method's file, signature and line;
then those files' source, scanned alone by each version and compared again only for equality.
No figure of section 5 had been computed.
