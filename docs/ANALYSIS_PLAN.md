# Analysis plan: what extraction cannot slim, and whether function injection can

> **Status: DRAFT, not yet registered.** Registration is the commit of this file with every
> **[DECIDE]** and **[FILL]** settled, before the sample is drawn. After that, any change is a
> dated amendment that says what had been seen when it was made.

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
5. why the split fails, where it does.

Reach and shape are what this study means by function injection being cheaper than extraction.
The two total costs count different things and are never compared (section 5).

It is descriptive. It tests no hypothesis, and it reports every figure it computes, whichever
way it points.

## 2. What was known when this was written

- **Seen.** SinewSlim's results on other samples: the long-method paper's corpora, among them
  `seed3`, a sample drawn by the same sampler with seed 3, on whose facts SinewSlim's search was
  checked for parity with the study's `split.py`. OfficeFloorSlim's scan of OfficeFloor's own
  repository (category 3, below: 8 of 119 stuck methods) and of one agent-grown Spring
  application (0 of 9).
- **Not seen.** Any repository of this study's sample: it has not been drawn.
- **Conflict of interest.** The author created OfficeFloor, SinewSlim and OfficeFloorSlim. This
  is why the sample is drawn by an independent tool with its seed fixed here, why repositories
  owned by the author are excluded, why every cost is the products' (this study computes none
  of its own), why the two costs are never put in a common unit, and why every case where
  function injection does worse is reported.

## 3. Sample

- **Tool.** `open-source-repository-sampler` **[FILL: the released version with `--as-of`]**,
  which draws a seeded, stratified simple random sample of GitHub repositories and pins each to
  a commit. The as-of option is proposed, not yet built (the sampler's
  `docs/proposals/as-of.md`).
- **As of.** **[DECIDE]** the date before which the code was written. Recommended: **1 June
  2021**, before GitHub Copilot's technical preview opened (29 June 2021). The latest
  defensible date is 30 November 2022, when ChatGPT was released and AI-written code entered
  general use. Every repository was created before the date, is pinned to the newest commit on
  its default branch's first-parent history before it, and is judged by the criteria there.
- **Frame.** Java repositories created before the as-of date, in three popularity tiers: high
  (over 5,000 stars), mid (1,000 to 5,000) and low (200 to 999).
- **Criteria** (as `seed3`'s): at least 50 functions, in at least 15 files; repositories owned by
  `officefloor` or `sagenschneider` excluded.
- **Size.** **[DECIDE]** 580 usable repositories, as `seed3`. Recommended: the same.
- **Seed.** **[DECIDE]** a new seed, not 3, so the sample is one nobody has looked at.
  Recommended: `20261101`. It is fixed here, and the first sample drawn with it is used.
- **Tiers** are drawn equally, so population estimates weight each stratum by population over
  usable, as the sampler's derivation gives them; between-tier comparisons need no weights.

## 4. Instruments

Every cost comes from the released products. This repository computes none.

- **OfficeFloorSlim** **[FILL: released version]**, its command line `officefloorslim scan
  --format json` (schema `officefloorslim-scan/2`), run once per repository at its pinned
  commit. It reports, for every long method, both columns:
  - **SinewSlim's assessment**, under SinewSlim's defaults, from the SinewSlim libraries it is
    built on (**[FILL: SinewSlim released version]**): trigger 26, target 25, at most 5
    parameters and 1 return per piece, records offered, no framework reading;
  - **the OfficeFloor split**, `officefloorslim-split/1`: every line in a function, none over
    25 code lines; its cost the values carried between functions, plus 1 per function and per
    flow; loops and lambda bodies never cut; at most 5 carried values per function. The cost
    model and its limits were decided before this plan (OfficeFloorSlim's `DESIGN.md`, *The
    OfficeFloor split*).
- **Scope.** **[DECIDE]** production Java only. Recommended: OfficeFloorSlim's defaults (every
  `.java`, leaving out `src/test`, `src/it`, `build`, `target`, `generated` and `node_modules`),
  plus `**/test/**` and `**/tests/**`, since open-source projects do not all follow Maven's
  layout.
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
| P1 | Per repository with at least one stuck method: its S2 over S1, and its category 3 over S1 |

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
- **The split's limits decide much.** Loops and lambda bodies are never cut. A different
  choice would change S2 and S3; the choice was made before this plan, for reasons of its own.
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
  excluded. Records arrived in Java 16 (March 2021) and were rare before 2022, so before the
  recommended date this is close to moot; with a later date it is a threat to state.
