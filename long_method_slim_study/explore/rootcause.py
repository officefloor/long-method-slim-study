"""The root cause of a category 4 method (combined split): the innermost obstacle the instrument
reports, read from the combined split's reason and detail.

The combined split's reason names the outer obstacle (a loop, try or switch it cannot cut between
functions, a statement over the target, carried values, a jump); its detail adds what SinewSlim says of
that statement as a function body of its own. The innermost of the two is the root cause, in one of
three groups:

- indivisible: one statement over the cap that nothing inside can move (an expression, a switch, ...)
- data: every cut needs too many values (inputs, two or more results, or more than 5 carried)
- control: a return, break or continue crosses every cut
"""
from __future__ import annotations

import re

LONG = "a single statement is longer"
JUMPS = "every run that would bring it under the cap has a return"
KIND = re.compile(r"nothing inside it can move: the (\w+(?: \w+)?) (?:statement )?at")
KINDS = {"return": "expression", "statement": "expression", "return statement": "expression",
         "labeled statement": "labelled statement", "if statement": "if", "switch statement": "switch",
         "try statement": "try", "loop": "loop", "synchronized block": "synchronized block"}


def inner_reason(detail: str | None) -> str:
    m = re.search(r"as a function body, SinewSlim: (.*)$", detail or "")
    return m.group(1) if m else ""


def root(combined: dict) -> tuple[str, str]:
    """(group, cause) for a category 4 method, from its combined split."""
    r, inner = combined["reason"], inner_reason(combined.get("detail"))
    if r == "carried":
        return "data", "carried"
    if r == "jumps" and not inner:
        return "control", "jump across every cut"
    if inner.startswith(LONG):
        k = KIND.search(inner)
        return "indivisible", KINDS.get(k.group(1), k.group(1)) if k else "unknown statement"
    if inner.startswith(JUMPS):
        return "control", "jumps inside a block"
    if "two or more results or needs more parameters" in inner:
        return "data", "inputs or results"
    if "needs more parameters" in inner:
        return "data", "inputs"
    if "two or more results" in inner:
        return "data", "results"
    if r == "long_statement" and not inner:
        return "indivisible", "unknown statement"
    return "other", r


def is_category4(m: dict) -> bool:
    return (m.get("combined_category") or {}).get("number") == 4
