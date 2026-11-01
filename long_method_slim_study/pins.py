"""Every value the study fixes in advance (docs/ANALYSIS_PLAN.md). The step scripts read them from
here and nowhere else, so the plan and the procedure cannot drift apart.

`REGISTERED` is False until the plan is committed with every DECIDE and FILL settled; step 2
refuses to draw the sample before then.
"""

# The plan's registration (section 7, step 1): set True in the commit that registers it.
REGISTERED = False

# Sample (section 3). DECIDE: the seed and the size; these are the plan's recommendations.
SEED = 20261101
TARGET = 580
LANGS = ["java"]
TIERS = ["high", "mid", "low"]
MIN_FUNCTIONS = 50
MIN_FILES_WITH_FUNCTIONS = 15
EXCLUDE_OWNERS = ["officefloor", "sagenschneider"]
SAMPLER_VERSION = "0.2.1"

# Instruments (section 4). FILL: OfficeFloorSlim's release, and its jar's sha256 from that
# GitHub Release, once both are published.
OFFICEFLOORSLIM_VERSION = None
OFFICEFLOORSLIM_JAR_SHA256 = None

# Scope (section 4). DECIDE: production Java only; these are the plan's recommendations
# (OfficeFloorSlim's defaults, plus test directories outside Maven's layout). The configuration
# files are read only for the classification.
INCLUDE = ["**/*.java", "**/*.yml", "**/*.yaml", "**/*.woof", "**/*.officefloor"]
EXCLUDE = ["**/src/test/**", "**/src/it/**", "**/build/**", "**/target/**", "**/generated/**",
           "**/node_modules/**", "**/test/**", "**/tests/**"]

# Analysis (section 6).
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261101
INTERVAL = 0.95


def unsettled() -> list[str]:
    """What is still to fill before the instruments can be fetched."""
    out = []
    if OFFICEFLOORSLIM_VERSION is None:
        out.append("OFFICEFLOORSLIM_VERSION")
    if OFFICEFLOORSLIM_JAR_SHA256 is None:
        out.append("OFFICEFLOORSLIM_JAR_SHA256")
    return out
