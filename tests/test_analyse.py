"""The analysis and the hook on made-up scans: what each measure counts, the pooling, the weights,
the intervals, and the repositories not scanned. No product is run."""
import csv
import json
import os
import tempfile
import unittest

from long_method_slim_study import analyse, scan


def method(status, cost=None, width=None, pieces=None, largest=None, feasible=True, seam=0, functions=2,
           largest_function=20, reason=None, category=None):
    s = {"status": status, "cost": cost}
    if cost is not None:
        s |= {"width": width, "pieces": pieces, "largest_piece": largest}
    o = {"feasible": feasible}
    if feasible:
        o |= {"worst_seam": seam, "functions": [{}] * functions, "largest_function": largest_function}
    else:
        o |= {"reason": reason}
    return {"path": "A.java", "type": "A", "signature": "f()", "line": 1, "sinewslim": s, "officefloor": o,
            "category": None if category is None else {"number": category}}


def scan_doc(methods, readings=None):
    return {"methods": methods, "long_methods": len(methods), "unparsed": [],
            "methods_by_reading": readings or {"conventional": 10 + len(methods)}}


class AnalyseTest(unittest.TestCase):

    def test_one_repository(self):
        r = analyse.repository(scan_doc([
            method("slimmable", cost=4, width=2, pieces=2, largest=20, seam=1, functions=3, largest_function=15),
            method("not_slimmable", feasible=True, seam=3, functions=4, category=3),
            method("not_slimmable", feasible=False, reason="loop", category=4),
            method("slimmable_with_record", cost=9, width=5, pieces=1, largest=24, seam=6, functions=2, category=2),
        ]))
        self.assertEqual((4, 3, 2), (r["long"], r["stuck"], r["stuck_planned"]))
        self.assertEqual({"3": 1, "4": 1, "2": 1}, r["category"])
        self.assertEqual([4], r["slim_costs"])  # a record's cost is not a plain slim cost
        self.assertEqual({"loop": 1}, r["reasons_long"])
        self.assertEqual(2, len(r["pairs"]))  # both have a plan: the first and the record one
        self.assertEqual([6], [w["officefloor_worst_seam"] for w in r["worse"]])  # 6 > 5

    def test_pooled_ratios_and_weights(self):
        rows = [
            {"tier": "high", "stuck": 4, "stuck_planned": 2, "category": {"3": 1}},
            {"tier": "low", "stuck": 6, "stuck_planned": 3, "category": {"3": 3}},
        ]
        self.assertEqual(0.5, analyse.ratio(rows, "stuck_planned", "stuck"))
        self.assertEqual(0.4, analyse.ratio(rows, "category.3", "stuck"))
        # the low tier weighs 9 to the high tier's 1: (1*1 + 9*3) / (1*4 + 9*6)
        self.assertAlmostEqual(28 / 58, analyse.ratio(rows, "category.3", "stuck", {"high": 1.0, "low": 9.0}))

    def test_bootstrap_is_seeded_and_brackets_the_estimate(self):
        rows = [{"tier": "t", "stuck": 10, "stuck_planned": k, "category": {}} for k in (2, 4, 6, 8)]
        a = analyse.bootstrap(rows, "stuck_planned", "stuck", None, 2000, 7, 0.95)
        b = analyse.bootstrap(rows, "stuck_planned", "stuck", None, 2000, 7, 0.95)
        self.assertEqual(a, b)
        self.assertLessEqual(a[0], 0.5)
        self.assertGreaterEqual(a[1], 0.5)

    def test_whole_analysis_lists_what_was_not_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            sample = os.path.join(d, "s.csv")
            with open(sample, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["full_name", "status", "tier", "commit"])
                w.writeheader()
                w.writerow({"full_name": "a/one", "status": "usable", "tier": "high", "commit": "c1"})
                w.writerow({"full_name": "b/two", "status": "usable", "tier": "low", "commit": "c2"})
                w.writerow({"full_name": "c/three", "status": "excluded", "tier": "low", "commit": "c3"})
            scans = os.path.join(d, "scans")
            os.makedirs(scans)
            with open(scan.out_path(scans, "a/one"), "w") as f:
                json.dump(scan_doc([method("not_slimmable", feasible=True, category=3)]), f)
            deriv = {"summary": {"per_stratum": {"java/high": {"population": 100, "usable": 10},
                                                 "java/low": {"population": 1000, "usable": 10}}}}
            r = analyse.analyse(scans, sample, deriv)
        self.assertEqual({"usable": 2, "scanned": 1, "not_scanned": ["b/two"], "excluded": 1, "error": 0}, r["sample"])
        self.assertEqual({"high": 10.0, "low": 100.0}, r["weights"])
        self.assertEqual(1.0, r["headline"]["category3_over_S1"]["pooled"])


class HookTest(unittest.TestCase):

    def test_command_reads_no_growth_and_the_pinned_scope(self):
        cmd = scan.command("/tmp/r", "/tmp/o.json")
        self.assertIn("--no-growth", cmd)
        self.assertEqual("json", cmd[cmd.index("--format") + 1])
        self.assertIn("**/tests/**", cmd)

    def test_the_clone_holds_every_file_the_scan_reads(self):
        from long_method_slim_study import pins
        for glob in pins.INCLUDE:
            self.assertIn(glob.rsplit("*", 1)[-1], pins.ONLY, glob)

    def test_names_never_nest(self):
        self.assertTrue(scan.out_path("out", "owner/name").endswith("owner__name.json"))


if __name__ == "__main__":
    unittest.main()
