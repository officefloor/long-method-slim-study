"""Every value the study fixes in advance (docs/ANALYSIS_PLAN.md). The step scripts read them from
here and nowhere else, so the plan and the procedure cannot drift apart.

`REGISTERED` is False until the plan is committed with every DECIDE and FILL settled; step 2
refuses to draw the sample before then.
"""

# The plan's registration (section 7, step 1): set True in the commit that registers it.
REGISTERED = True

# Sample (section 3): the seed and the size, decided 1 November 2026.
SEED = 20261101
TARGET = 580
LANGS = ["java"]
TIERS = ["high", "mid", "low"]
MIN_FUNCTIONS = 50
MIN_FILES_WITH_FUNCTIONS = 15
EXCLUDE_OWNERS = ["officefloor", "sagenschneider"]
# The date the code was written before (section 3, As of): decided 1 November 2026, six months
# before 1 June 2021, itself before GitHub Copilot's technical preview (29 June 2021).
AS_OF = "2020-12-01"
# The sampler's release with --as-of (v0.3.0, 25c4bf6, on PyPI 1 November 2026).
SAMPLER_VERSION = "0.3.0"

# Instruments (section 4): OfficeFloorSlim 0.5.2 (released 3 November 2026, built on SinewSlim
# 0.2.3 from Maven Central), with the combined split, and its jar's sha256 from that GitHub
# Release. Amendment 1 (2 November 2026): was 0.3.0 (sha256 e8177237...), whose combined split
# took hours on long flat methods. Amendment 2 (3 November 2026): was 0.5.0 (sha256 0fcebfd3...),
# which still took hours on generated tables of thousands of statements. Amendment 3 (3 November
# 2026): was 0.5.1 (sha256 9f3d8819...), which changed the results of 2 repositories; 0.5.2 gives
# 0.5.0's, as 0.5.0 gave 0.3.0's.
OFFICEFLOORSLIM_VERSION = "0.5.2"
OFFICEFLOORSLIM_JAR_SHA256 = "513b669f61c72de0d6ad4640dc1c268e6064dccc73190ae1bdfaf7ffbb1614d9"

# Scope (section 4): production Java, no tests, decided 1 November 2026 (OfficeFloorSlim's
# defaults, plus test directories outside Maven's layout). The configuration files are read only
# for the classification.
INCLUDE = ["**/*.java", "**/*.yml", "**/*.yaml", "**/*.woof", "**/*.officefloor"]
EXCLUDE = ["**/src/test/**", "**/src/it/**", "**/build/**", "**/target/**", "**/generated/**",
           "**/node_modules/**", "**/test/**", "**/tests/**"]

# What each clone downloads (the sampler's `run --only`, a sparse checkout): only the files the
# scan reads. The rest of each repository is never fetched.
ONLY = [".java", ".yml", ".yaml", ".woof", ".officefloor"]

# Hypotheses (section 6, Hypotheses). H1: category 3 under the combined split is at least this
# share of the stuck methods, and at least this many (the go/no-go bar, fixed 31 October 2026).
H1_SHARE = 0.25
H1_MINIMUM = 30
# H2: of the long methods SinewSlim slims, the share where the combined split chooses injection and
# its sum is strictly lower than SinewSlim's cost plus 1. Decided 1 November 2026: "none", an
# estimate with its interval and no threshold, since OfficeFloor's own code had already given 95
# of 327 (29%) (section 2) and a threshold chosen knowing it would not test anything.
H2_SHARE = "none"

# Analysis (section 6).
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261101
INTERVAL = 0.95


def unsettled() -> list[str]:
    """What is still to fill before the instruments can be fetched."""
    out = []
    if SAMPLER_VERSION is None:
        out.append("SAMPLER_VERSION")
    if OFFICEFLOORSLIM_VERSION is None:
        out.append("OFFICEFLOORSLIM_VERSION")
    if OFFICEFLOORSLIM_JAR_SHA256 is None:
        out.append("OFFICEFLOORSLIM_JAR_SHA256")
    if H2_SHARE is None:
        out.append("H2_SHARE")
    return out
