"""Every value the study fixes in advance (docs/ANALYSIS_PLAN.md). The step scripts read them from
here and nowhere else, so the plan and the procedure cannot drift apart.

`REGISTERED` is False until the plan is committed with every DECIDE and FILL settled; step 2
refuses to draw the sample before then.
"""

# The plan's registration (section 7, step 1): set True in the commit that registers it.
REGISTERED = False

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

# Instruments (section 4): OfficeFloorSlim 0.2.1 (released 1 November 2026, built on SinewSlim
# 0.2.0 from Maven Central), and its jar's sha256 from that GitHub Release.
OFFICEFLOORSLIM_VERSION = "0.2.1"
OFFICEFLOORSLIM_JAR_SHA256 = "80b293a6aaeafd2a0cd138360554c5371e62a6ce6b80c47d9a8ce5d10b67d4e4"

# Scope (section 4): production Java, no tests, decided 1 November 2026 (OfficeFloorSlim's
# defaults, plus test directories outside Maven's layout). The configuration files are read only
# for the classification.
INCLUDE = ["**/*.java", "**/*.yml", "**/*.yaml", "**/*.woof", "**/*.officefloor"]
EXCLUDE = ["**/src/test/**", "**/src/it/**", "**/build/**", "**/target/**", "**/generated/**",
           "**/node_modules/**", "**/test/**", "**/tests/**"]

# What each clone downloads (the sampler's `run --only`, a sparse checkout): only the files the
# scan reads. The rest of each repository is never fetched.
ONLY = [".java", ".yml", ".yaml", ".woof", ".officefloor"]

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
    return out
