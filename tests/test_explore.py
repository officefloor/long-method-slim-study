import unittest

from long_method_slim_study.explore import domains, rootcause
from long_method_slim_study.explore.harness import blocking_lines
from long_method_slim_study.explore.report import refine

LONG = ("the loop at lines 10-60 (45 lines); as a function body, SinewSlim: a single statement is longer than the "
        "cap and nothing inside it can move: the switch statement at lines 12-58 (44 lines)")
JUMPY = ("the loop at lines 61-120 (57 lines); as a function body, SinewSlim: every run that would bring it under "
         "the cap has a return, break or continue leaving it (early returns, or a switch of returns)")


class RootCauseTest(unittest.TestCase):

    def test_innermost_obstacle(self):
        self.assertEqual(rootcause.root({"reason": "loop", "detail": LONG}), ("indivisible", "switch"))
        self.assertEqual(rootcause.root({"reason": "loop", "detail": JUMPY}), ("control", "jumps inside a block"))
        self.assertEqual(rootcause.root({"reason": "carried", "detail": None}), ("data", "carried"))
        self.assertEqual(rootcause.root({"reason": "jumps", "detail": None}), ("control", "jump across every cut"))
        ret = ("the return at lines 111-144 (34 lines); as a function body, SinewSlim: a single statement is longer "
               "than the cap and nothing inside it can move: the return statement at lines 111-144 (34 lines)")
        self.assertEqual(rootcause.root({"reason": "long_statement", "detail": ret}), ("indivisible", "expression"))
        inputs = "the try at lines 1-90 (80 lines); as a function body, SinewSlim: every cut needs more parameters than the limit"
        self.assertEqual(rootcause.root({"reason": "try", "detail": inputs}), ("data", "inputs"))

    def test_blocking_lines(self):
        self.assertEqual(blocking_lines(LONG), ({"start": 10, "end": 60}, {"start": 12, "end": 58}))
        self.assertEqual(blocking_lines(JUMPY), ({"start": 61, "end": 120}, None))
        self.assertEqual(blocking_lines(None), (None, None))


class DomainTest(unittest.TestCase):

    def test_first_rule_wins_and_short_words_are_whole(self):
        self.assertEqual(domains.domain({"description": "A SQL parser library"}, "x/y")[0], "database and query")
        self.assertEqual(domains.domain({"description": "Google core libraries for Java"}, "google/guava")[0],
                         "frameworks and libraries")
        self.assertEqual(domains.domain({"description": "Suite of tools for deep learning on the JVM"}, "a/dl")[0],
                         "numeric, scientific and ML")
        # "ide" must not match inside "provide"
        self.assertNotEqual(domains.domain({"description": "provides things"}, "a/b")[0], "language tooling")
        self.assertEqual(domains.domain({}, "a/zzz")[0], "unknown")


class RefineTest(unittest.TestCase):

    def h(self, **kw):
        return {"found": True, "limits": {k: {"combined": False, "conventional": "NOT_SLIMMABLE", "injection": False}
                                          for k in ("5", "6", "7", "8", "10")}, **kw}

    def test_switch_and_if(self):
        sw = {"switch": {"cases_over_target": 0, "max_case_lines": 2}}
        self.assertTrue(refine("indivisible", "switch", self.h(inner=sw))[0].startswith("switch: flat table"))
        leaf = {"if": {"else_if": 0, "branches": 2}, "outputs": 0, "jumps": {"return": 0}}
        self.assertTrue(refine("indivisible", "if", self.h(inner=leaf))[0].startswith("if: branchy leaf"))
        out = {"if": {"else_if": 1, "branches": 3}, "outputs": 2, "jumps": {"return": 1}}
        self.assertEqual(refine("indivisible", "if", self.h(inner=out))[0], "if: passes values and jumps")

    def test_data_limit(self):
        h = self.h()
        h["limits"]["7"]["combined"] = True
        self.assertEqual(refine("data", "inputs", h)[0], "data: plan at 7")
        self.assertEqual(refine("data", "inputs", self.h())[0], "data: no plan at 10")
        self.assertEqual(refine("data", "inputs", None)[0], "not re-read")



class ComplexityTest(unittest.TestCase):

    def test_flow_divergence_and_roles(self):
        from long_method_slim_study.explore import complexity
        # calls: [arguments, kind, resolution, target, line]; resolution 0 is internal, 1 the JDK
        rec = {"params": 2, "calls": [[1, 0, 0, 3, 10], [3, 0, 0, 3, 20], [5, 0, 1, -1, 12]]}
        self.assertEqual(complexity.flow(rec), {"in": 3, "out": 6, "d": 3, "role": "junction", "budget_calls": 0})
        # the statement on lines 5..15 with 4 inputs: one internal call (1 + 1) against 1 + 4
        self.assertEqual(complexity.flow(rec, 5, 15, 4)["role"], "catchment")
        self.assertEqual(complexity.flow({"params": 0, "calls": [[0, 0, 0, 1, 1]]})["role"], "pipe")

    def test_bins_and_groups(self):
        from long_method_slim_study.explore import complexity
        self.assertEqual(complexity.bin_of(26), "26-35")
        self.assertEqual(complexity.bin_of(400), "301+")
        m = {"sinewslim": {"status": "not_slimmable"}, "combined_category": {"number": 4}}
        self.assertEqual(complexity.group_of(m), "category 4")
        self.assertEqual(complexity.group_of({"sinewslim": {"status": "slimmable"}}), "slimmable")

    def test_scope(self):
        from long_method_slim_study.explore.measure import in_scope
        self.assertTrue(in_scope("src/main/java/a/TestRunner.java"))
        self.assertFalse(in_scope("core/src/test/java/a/A.java"))
        self.assertFalse(in_scope("x/generated/A.java"))


class ControlTest(unittest.TestCase):

    NONE = {"return": 0, "break": 0, "continue": 0, "yield": 0}

    def h(self, **kw):
        return {"found": True, "method_jumps": dict(self.NONE), "method_all_jumps": dict(self.NONE),
                "method_lambda_jumps": 0, "top_statements": 3, "constructor_delegation_only": False, **kw}

    def test_regroup(self):
        from long_method_slim_study.explore.report import regroup
        top = "jump across every cut"
        self.assertEqual(regroup("control", top, self.h(constructor_delegation_only=True, top_statements=1))[0],
                         "indivisible")
        self.assertEqual(regroup("control", top, self.h(method_lambda_jumps=2))[1],
                         "returns inside a lambda or anonymous class")
        self.assertEqual(regroup("control", top, self.h(top_statements=1))[1],
                         "a one-statement body (one return or expression)")
        # a single return statement: its return crosses no cut
        ret = {**self.NONE, "return": 1}
        self.assertEqual(regroup("control", top, self.h(top_statements=1, only_statement="ReturnStmt",
                                                        method_all_jumps=ret))[0], "indivisible")
        # but a single loop with a return in it is control
        self.assertEqual(regroup("control", top, self.h(top_statements=1, only_statement="ForStmt",
                                                        method_all_jumps=ret))[0], "control")
        # a jump anywhere keeps it control; version 1 results and other groups are left alone
        self.assertEqual(regroup("control", top, self.h(method_all_jumps={**self.NONE, "break": 1})),
                         ("control", top))
        self.assertEqual(regroup("control", top, {"found": True}), ("control", top))
        self.assertEqual(regroup("data", "inputs", self.h(top_statements=1)), ("data", "inputs"))

    def test_nested_jump(self):
        outer = {"kind": "ForStmt", "jumps": dict(self.NONE), "all_jumps": {**self.NONE, "break": 2}}
        self.assertEqual(refine("control", "jumps inside a block", self.h(outer=outer))[0],
                         "control: nested break/continue, in a loop")
        outer = {"kind": "SynchronizedStmt", "jumps": {**self.NONE, "return": 1}, "all_jumps": {**self.NONE, "return": 1}}
        self.assertEqual(refine("control", "jumps inside a block", self.h(outer=outer))[0],
                         "control: return, in a synchronized block")


if __name__ == "__main__":
    unittest.main()
