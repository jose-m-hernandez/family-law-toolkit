"""Tests for the step 1 guideline computation (Family Code 4055)."""

import ast
import inspect
import json
import unittest
from fractions import Fraction
from pathlib import Path

from family_law_toolkit.support import guideline
from family_law_toolkit.support.guideline import compute, fixed, money

GOLDEN_PATH = Path(__file__).resolve().parent / "golden" / "guideline_step1.json"
GUIDELINE_PATH = Path(guideline.__file__)
GOLDEN_STEP2_PATH = Path(__file__).resolve().parent / "golden" / "guideline_step2.json"


def load_cases():
    with GOLDEN_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)["cases"]


def run(inputs):
    return compute(
        inputs["a_ndi"],
        inputs["b_ndi"],
        inputs["a_time_percent"],
        inputs["children"],
        inputs["minimum_wage_hourly"],
    )


def quick(a_ndi="4000.00", b_ndi="2000.00", time="0", children=1, wage="21.00", flag=None):
    if flag is None:
        return compute(a_ndi, b_ndi, time, children, wage)
    return compute(a_ndi, b_ndi, time, children, wage, same_time_sharing_arrangement=flag)


class GuidelineTests(unittest.TestCase):
    def test_golden_cases(self):
        for case in load_cases():
            with self.subTest(case=case["id"]):
                expected = case["expected"]
                result = run(case["inputs"])
                self.assertEqual(money(result.tn), expected["tn"])
                self.assertEqual(result.high_earner, expected["high_earner"])
                self.assertEqual(result.h_percent, Fraction(expected["h_percent"]))
                self.assertEqual(result.k_row, expected["k_row"])
                self.assertEqual(fixed(result.k, 6), expected["k"])
                self.assertEqual(money(result.cs_formula), expected["cs_formula"])
                self.assertEqual(result.multiplier, Fraction(expected["multiplier"]))
                self.assertEqual(money(result.cs_total), expected["cs_total"])
                self.assertEqual(result.payer, expected["payer"])
                self.assertEqual(money(result.support), expected["support"])
                lia = expected["lia"]
                self.assertEqual(money(result.lia.threshold), lia["threshold"])
                self.assertEqual(result.lia.applies, lia["applies"])
                self.assertEqual(money(result.lia.max_reduction), lia["max_reduction"])
                self.assertEqual(money(result.lia.range_low), lia["range_low"])
                self.assertEqual(money(result.lia.range_high), lia["range_high"])

    def test_statute_example_k(self):
        # FC 4055(b)(3)'s own example: TN 1,000, H% 20 and H% 80, K is 0.21.
        for time in ("20", "80"):
            with self.subTest(h_percent=time):
                result = quick(a_ndi="1000.00", b_ndi="0.00", time=time)
                self.assertEqual(result.h_percent, Fraction(time))
                self.assertEqual(fixed(result.k, 2), "0.21")

    def test_k_table_rows(self):
        expected = [
            ("2900", 1), ("2900.01", 2), ("5000", 2), ("5000.01", 3),
            ("10000", 3), ("10000.01", 4), ("15000", 4), ("15000.01", 5),
        ]
        for total, row in expected:
            with self.subTest(tn=total):
                self.assertEqual(quick(a_ndi=total, b_ndi="0").k_row, row)

    def test_multiplier_table(self):
        expected = ["1", "1.6", "2", "2.3", "2.5", "2.625", "2.75", "2.813", "2.844", "2.86"]
        for children, value in enumerate(expected, start=1):
            with self.subTest(children=children):
                self.assertEqual(quick(children=children).multiplier, Fraction(value))
        for children in (0, 11):
            with self.subTest(children=children):
                with self.assertRaises(ValueError):
                    quick(children=children)

    def test_equal_incomes_symmetric(self):
        first = quick(a_ndi="2500.00", b_ndi="2500.00", time="30")
        swapped = quick(a_ndi="2500.00", b_ndi="2500.00", time="70")
        self.assertGreater(first.support, 0)
        self.assertEqual(first.support, swapped.support)
        # Swapping the labels swaps the parents: the same real parent pays.
        self.assertEqual(first.payer, "A")
        self.assertEqual(swapped.payer, "B")

    def test_statute_example_k_exact(self):
        # Exact K for the FC 4055(b)(3) example; a typo in a row coefficient fails.
        for time in ("20", "80"):
            with self.subTest(h_percent=time):
                result = quick(a_ndi="1000.00", b_ndi="0.00", time=time)
                self.assertEqual(result.k, Fraction(2934281, 13809500))

    def test_k_exact_per_row(self):
        # Synthetic round totals, H% 0 (K is the row fraction), written out
        # independently of the K_ROWS table.
        expected = [
            ("2900", 1, Fraction(165, 1000) + Fraction(2900, 82857)),
            ("4000", 2, Fraction(131, 1000) + Fraction(4000, 42149)),
            ("8000", 3, Fraction(1, 4)),
            ("12000", 4, Fraction(1, 10) + Fraction(1499, 12000)),
            ("20000", 5, Fraction(12, 100) + Fraction(1200, 20000)),
        ]
        for total, row, fraction in expected:
            with self.subTest(tn=total):
                result = quick(a_ndi=total, b_ndi="0.00", time="0")
                self.assertEqual(result.k_row, row)
                self.assertEqual(result.k, fraction)

    def test_fifty_percent_boundary_both_k_branches_agree(self):
        # H% = 50 is the seam between 1 + H% and 2 - H%: both give the same K.
        result = quick(a_ndi="1000.00", b_ndi="1000.00", time="50")
        self.assertEqual(result.h_percent, Fraction(50))
        h_fraction = result.h_percent / 100
        self.assertEqual(1 + h_fraction, 2 - h_fraction)
        fraction = guideline.row_fraction(result.k_row, result.tn)
        self.assertEqual(result.k, (1 + h_fraction) * fraction)
        self.assertEqual(result.k, (2 - h_fraction) * fraction)
        # The same holds when Parent B is the high earner.
        other = quick(a_ndi="500.00", b_ndi="1500.00", time="50")
        self.assertEqual(other.high_earner, "B")
        self.assertEqual(other.h_percent, Fraction(50))
        self.assertEqual(
            other.k, (2 - other.h_percent / 100) * guideline.row_fraction(other.k_row, other.tn)
        )

    def test_tie_labels_parent_a_high_earner(self):
        for time in ("30", "50", "70"):
            with self.subTest(time=time):
                result = quick(a_ndi="1000.00", b_ndi="1000.00", time=time)
                self.assertEqual(result.high_earner, "A")
                self.assertEqual(result.h_percent, Fraction(time))

    def test_fixed_rounds_half_up_away_from_zero(self):
        cases = [
            (Fraction(1, 200), "0.01"),
            (Fraction(-1, 200), "-0.01"),
            (Fraction(3, 200), "0.02"),
            (Fraction(-3, 200), "-0.02"),
            (Fraction(199, 40000), "0.00"),  # 0.004975, just below a half-cent
            (Fraction(-199, 40000), "0.00"),
            (Fraction(2999, 200000), "0.01"),  # 0.014995, just below 0.015
            (Fraction(201, 40000), "0.01"),  # 0.005025, just above a half-cent
            (Fraction(-201, 40000), "-0.01"),
            (Fraction(199, 200), "1.00"),  # 0.995
        ]
        for value, text in cases:
            with self.subTest(value=value):
                self.assertEqual(fixed(value, 2), text)
                self.assertEqual(money(value), text)

    def test_zero_incomes(self):
        result = quick(a_ndi="0", b_ndi="0")
        self.assertEqual(money(result.support), "0.00")
        self.assertEqual(result.payer, "none")
        self.assertFalse(result.lia.applies)

    def test_negative_result_lower_earner_pays(self):
        case = next(c for c in load_cases() if c["id"] == "G6")
        expected = case["expected"]
        result = run(case["inputs"])
        self.assertLess(result.cs_total, 0)
        self.assertEqual(result.high_earner, expected["high_earner"])
        self.assertGreater(result.h_percent, 50)
        self.assertEqual(result.payer, expected["payer"])
        self.assertNotEqual(result.payer, result.high_earner)
        self.assertEqual(money(result.support), expected["support"])
        self.assertTrue(result.lia.applies)

    def test_lia_strictly_less_than(self):
        at_threshold = quick(a_ndi="3640.00", b_ndi="0.00")
        self.assertFalse(at_threshold.lia.applies)
        below = quick(a_ndi="3639.99", b_ndi="0.00")
        self.assertTrue(below.lia.applies)

    def test_lia_threshold_from_wage(self):
        self.assertEqual(quick(wage="21.00").lia.threshold, Fraction(3640))
        self.assertEqual(
            quick(wage="19.75").lia.threshold, Fraction("19.75") * 40 * 52 / 12
        )

    def test_lia_range(self):
        result = quick(a_ndi="1850.00", b_ndi="650.00", time="20", children=3)
        self.assertTrue(result.lia.applies)
        self.assertEqual(result.lia.range_high, result.support)
        self.assertEqual(
            result.lia.range_low, result.support - result.lia.max_reduction
        )
        self.assertGreater(result.lia.max_reduction, 0)

    def test_compute_takes_five_inputs_and_one_optional(self):
        # No parameter can request the FC 4055(b)(6) default-proceeding rule.
        parameters = inspect.signature(compute).parameters
        self.assertEqual(
            list(parameters),
            ["a_ndi", "b_ndi", "a_time_percent", "children", "minimum_wage_hourly",
             "same_time_sharing_arrangement"],
        )
        self.assertIsNone(parameters["same_time_sharing_arrangement"].default)
        for name in list(parameters)[:5]:
            self.assertIs(parameters[name].default, inspect.Parameter.empty)

    def test_same_time_sharing_arrangement_values(self):
        for value in (None, "yes", "no"):
            with self.subTest(value=value):
                result = compute("4000.00", "2000.00", "0", 2, "21.00",
                                 same_time_sharing_arrangement=value)
                self.assertEqual(result.same_time_sharing_arrangement, value)
        for value in ("maybe", "YES", "", True, 1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as caught:
                    compute("4000.00", "2000.00", "0", 2, "21.00",
                            same_time_sharing_arrangement=value)
                self.assertIn("same_time_sharing_arrangement", str(caught.exception))

    def test_invalid_inputs_rejected(self):
        bad = [
            {"a_ndi": "-1"}, {"b_ndi": "-0.01"},
            {"a_ndi": "NaN"}, {"b_ndi": "Infinity"}, {"a_ndi": "-Infinity"},
            {"a_ndi": "abc"}, {"a_ndi": 4000},
            {"time": "-1"}, {"time": "100.01"}, {"time": "NaN"},
            {"children": 0}, {"children": 11}, {"children": True}, {"children": "1"},
            {"wage": "0"}, {"wage": "-21.00"}, {"wage": "Infinity"},
            {"a_ndi": "4000.001"}, {"b_ndi": "1.234"},
            {"time": "20.001"}, {"wage": "21.005"},
            {"a_ndi": "1E+30"},
        ]
        names = {
            "a_ndi": "a_ndi", "b_ndi": "b_ndi", "time": "a_time_percent",
            "children": "children", "wage": "minimum_wage_hourly",
        }
        for kwargs in bad:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError) as caught:
                    quick(**kwargs)
                (key, value), = kwargs.items()
                self.assertIn(names[key], str(caught.exception))
                if isinstance(value, str):
                    self.assertNotIn(value, str(caught.exception))

    def test_exact_arithmetic_no_float(self):
        tree = ast.parse(GUIDELINE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                self.assertNotIsInstance(node.value, float)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotEqual(node.func.id, "float")

    def test_golden_step2_allocation(self):
        with GOLDEN_STEP2_PATH.open(encoding="utf-8") as handle:
            cases = json.load(handle)["cases"]
        self.assertEqual([case["id"] for case in cases], ["S1", "S2", "S3", "S4", "S5"])
        for case in cases:
            with self.subTest(case=case["id"]):
                inputs = case["inputs"]
                expected = case["expected"]
                result = compute(
                    inputs["a_ndi"], inputs["b_ndi"], inputs["a_time_percent"],
                    inputs["children"], inputs["minimum_wage_hourly"],
                    same_time_sharing_arrangement=inputs["same_time_sharing_arrangement"],
                )
                self.assertEqual(money(result.support), expected["support"])
                allocation = guideline.allocation(result)
                ends = {"top": allocation.top}
                if allocation.bottom is not None:
                    ends["bottom"] = allocation.bottom
                self.assertEqual(set(ends), set(expected["allocation"]))
                for name, end in ends.items():
                    want = expected["allocation"][name]
                    self.assertEqual(
                        [guideline.cents_text(c) for c in end.cumulative], want["cumulative"]
                    )
                    self.assertEqual(
                        [guideline.cents_text(c) for c in end.per_child], want["per_child"]
                    )

    def test_allocation_exact_amounts_and_rounding_rule(self):
        # R8 on S5: the exact cumulative amounts are cs_formula x each multiplier;
        # per-child amounts are differences of the DISPLAYED running totals.
        result = compute("12105.04", "1639.79", "60", 4, "21.00",
                         same_time_sharing_arrangement="yes")
        allocation = guideline.allocation(result)
        self.assertIsNone(allocation.bottom)
        exact = allocation.top.exact_cumulative
        for count, value in enumerate(exact, start=1):
            self.assertEqual(value, abs(result.cs_formula) * guideline.MULTIPLIERS[count])
        shown = allocation.top.cumulative
        self.assertEqual(shown[-1], 259719)
        self.assertEqual(allocation.top.per_child[0], shown[0])
        self.assertEqual(
            list(allocation.top.per_child[1:]),
            [b - a for a, b in zip(shown, shown[1:])],
        )
        self.assertEqual(sum(allocation.top.per_child), shown[-1])
        # Rounding each exact difference alone does NOT add to the total here.
        steps = [exact[0]] + [b - a for a, b in zip(exact, exact[1:])]
        alone = [int((2 * s * 100 + 1) // 2) for s in steps]  # half-up for positives
        self.assertNotEqual(sum(alone), shown[-1])

    def test_allocation_rounding_is_half_up_at_exact_half_cents(self):
        # Python's round() is half-even and would give 2 for 0.025.
        self.assertEqual(guideline._cents(Fraction(1, 200)), 1)  # 0.005
        self.assertEqual(guideline._cents(Fraction(5, 200)), 3)  # 0.025
        self.assertEqual(guideline._cents(Fraction(7, 200)), 4)  # 0.035
        self.assertEqual(guideline._cents(Fraction(1, 300)), 0)  # 0.00333..., below the half

    def test_allocation_bottom_end_is_support_times_one_minus_fraction(self):
        result = compute("2258.50", "612.53", "45", 3, "21.00",
                         same_time_sharing_arrangement="yes")
        bottom = guideline.allocation(result).bottom
        fraction = (result.lia.threshold - result.a_ndi) / result.lia.threshold
        self.assertEqual(bottom.exact_cumulative[-1], result.lia.range_low)
        for count, value in enumerate(bottom.exact_cumulative, start=1):
            self.assertEqual(
                value,
                abs(result.cs_formula) * guideline.MULTIPLIERS[count] * (1 - fraction),
            )

    def test_allocation_is_none_unless_it_applies(self):
        self.assertIsNone(guideline.allocation(quick(children=3)))
        self.assertIsNone(guideline.allocation(quick(children=3, flag="no")))
        self.assertIsNone(guideline.allocation(quick(children=1, flag="yes")))
        self.assertIsNone(guideline.allocation(quick("0", "0", "0", 3, flag="yes")))
        self.assertIsNotNone(guideline.allocation(quick(children=3, flag="yes")))

    def test_allocation_negative_total_uses_the_absolute_amount(self):
        result = compute("8208.09", "5127.40", "65", 3, "21.00",
                         same_time_sharing_arrangement="yes")
        self.assertLess(result.cs_total, 0)
        end = guideline.allocation(result).top
        self.assertEqual(sum(end.per_child), end.cumulative[-1])
        self.assertTrue(all(c > 0 for c in end.per_child))


if __name__ == "__main__":
    unittest.main()
