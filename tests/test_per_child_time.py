"""Tests for one share of time per child (FC 4055(b)(1)(D)); invented numbers only.

Expected values are literal Fractions worked out by hand, never recomputed
with the calculator's own helpers.
"""

import dataclasses
import json
import re
import unittest
from fractions import Fraction
from pathlib import Path

from family_law_toolkit.support import report
from family_law_toolkit.support.guideline import allocation, compute
from family_law_toolkit.support.report import (
    NOTE_PER_CHILD_DIFFERENT,
    NOTE_PER_CHILD_DIFFERENT_SHARES,
    NOTE_PER_CHILD_NO_FLAG,
    render_report,
)
from tests.test_report import run_cli

ROOT = Path(__file__).resolve().parent.parent
P1 = ("6000.00", "2000.00")
LIA = ("3000.00", "500.00")
WAGE = "21.00"
FLAG = "--same-time-sharing-arrangement"

GC_DIFFERENT_SHARES = "This toolkit reads different percentages of time for different children as different time-sharing arrangements, so the per-child allocation (FC 4055(b)(8)) does not apply."

S_READ = (
    "  This toolkit reads the average in FC 4055(b)(1)(D) as the high earner's "
    "percentages of time with each child, added up and divided by the number "
    "of children. The formula uses the exact average; H% above is shown "
    "rounded to two decimals."
)
S_CONTRA = (
    "a_time_percent gives different percentages per child, and "
    "same_time_sharing_arrangement is yes: the two inputs contradict each other"
)
S_CONTRA_CLI = (
    "python3 -m family_law_toolkit.support: error: --a-time-percent gives "
    "different percentages per child, and --same-time-sharing-arrangement is "
    "yes: the two inputs contradict each other"
)
S_COUNT = (
    "a_time_percent needs one percentage per child: the number of "
    "percentages differs from children"
)
S_COUNT_CLI = (
    "python3 -m family_law_toolkit.support: error: --a-time-percent needs one "
    "percentage per child: the number of percentages differs from --children"
)
S_HELP = "Repeat the flag once per child to enter a share for each child."


def cli_flags(a_ndi, b_ndi, shares, children, wage=WAGE):
    args = ["--a-ndi", a_ndi, "--b-ndi", b_ndi]
    for share in shares:
        args += ["--a-time-percent", share]
    args += ["--children", str(children), "--minimum-wage-hourly", wage]
    return args


class PerChildTimeTests(unittest.TestCase):
    def test_mean_is_exact_and_unrounded(self):
        result = compute(*P1, ["50", "50", "51"], 3, WAGE)
        self.assertEqual(result.h_percent, Fraction(151, 3))
        self.assertNotEqual(result.h_percent, Fraction("50.33"))
        self.assertEqual(result.a_time_percent, Fraction(151, 3))
        self.assertEqual(
            result.a_time_percent_by_child, (Fraction(50), Fraction(50), Fraction(51))
        )
        self.assertEqual(result.high_earner, "A")
        self.assertEqual(result.k_row, 3)
        self.assertEqual(result.k, Fraction(449, 1200))
        self.assertEqual(result.cs_formula, Fraction(33226, 45))
        self.assertEqual(result.multiplier, 2)
        self.assertEqual(result.cs_total, Fraction(66452, 45))
        self.assertEqual(result.payer, "A")
        self.assertIs(result.lia.applies, False)

    def test_mean_above_50_uses_the_two_minus_h_branch(self):
        # The exact mean 50.33...% is above 50; a mean rounded to a whole
        # percent (50) would not be, and would take the (1 + H%) branch.
        result = compute(*P1, ["50", "50", "51"], 3, WAGE)
        self.assertEqual(result.k, (2 - Fraction(151, 300)) * Fraction(1, 4))
        self.assertNotEqual(result.k, Fraction(3, 8))

    def test_report_shows_the_mean_rounded_and_the_reading_line(self):
        text = render_report(compute(*P1, ["50", "50", "51"], 3, WAGE))
        lines = text.split("\n")
        for expected in (
            "  Parent A's share of time, by child: 50%, 50%, 51%",
            "  High earner's share of time, H% (FC 4055(b)(1)(D)): 50.33%",
            "  K (FC 4055(b)(3)): 0.374167",
            "  Formula result, CS = K[HN - (H%)(TN)] (FC 4055(a)): 738.36",
            "  CS times multiplier (FC 4055(b)(4)): 1476.71",
        ):
            self.assertIn(expected, lines)
        h_index = lines.index(
            "  High earner's share of time, H% (FC 4055(b)(1)(D)): 50.33%"
        )
        self.assertEqual(lines[h_index + 1], report.READING_AVERAGE_LINE)
        self.assertEqual(report.READING_AVERAGE_LINE, S_READ)
        self.assertFalse(
            [line for line in lines if line.startswith("  Parent A's share of time: ")]
        )
        self.assertEqual(text.count(NOTE_PER_CHILD_DIFFERENT_SHARES), 1)
        self.assertNotIn(NOTE_PER_CHILD_DIFFERENT, text)
        self.assertEqual(report.NOTE_PER_CHILD_DIFFERENT_SHARES, GC_DIFFERENT_SHARES)

    def test_averaging_a_then_taking_the_high_earner_equals_the_other_order(self):
        cases = (
            ("2000.00", "6000.00", ["30", "45", "50"]),
            ("6000.00", "2000.00", ["30", "45", "50"]),
            ("6000.00", "2000.00", ["0", "100", "33.33"]),
            ("2000.00", "6000.00", ["12.5", "80", "61.25", "0"]),
        )
        for index, (a_ndi, b_ndi, shares) in enumerate(cases):
            with self.subTest(case=index):
                result = compute(a_ndi, b_ndi, shares, len(shares), WAGE)
                a = [Fraction(x) for x in shares]
                a_high = result.high_earner == "A"
                self.assertEqual(a_high, Fraction(a_ndi) >= Fraction(b_ndi))
                high = a if a_high else [100 - x for x in a]
                self.assertEqual(result.h_percent, sum(high) / len(high))
                other_order = sum(a) / len(a) if a_high else 100 - sum(a) / len(a)
                self.assertEqual(result.h_percent, other_order)
                if index == 0:
                    self.assertEqual(result.h_percent, Fraction(175, 3))

    def test_terminating_mean_matches_the_single_share_path(self):
        fields = (
            "tn", "high_earner", "h_percent", "k_row", "k", "cs_formula",
            "multiplier", "cs_total", "payer", "support", "lia",
        )
        pairs = ((P1, ["30", "40"], "35", 2), (LIA, ["20", "30"], "25", 2))
        for index, (money_pair, shares, single, children) in enumerate(pairs):
            with self.subTest(case=index):
                listed = compute(*money_pair, shares, children, WAGE)
                plain = compute(*money_pair, single, children, WAGE)
                for field in fields:
                    self.assertEqual(getattr(listed, field), getattr(plain, field), field)
                if index == 1:
                    self.assertTrue(listed.lia.applies)

    def test_different_shares_show_no_allocation_and_say_b8_does_not_apply(self):
        single_text = render_report(compute(*P1, "35", 2, WAGE))
        support_prefix = "  Support amount (FC 4055(a), (b)(4)): "
        single_support = [l for l in single_text.split("\n") if l.startswith(support_prefix)]
        self.assertEqual(len(single_support), 1)
        # Flag unset: the toolkit's own conclusion, so the reading line.
        # Flag "no": it repeats what the user said, so the old note.
        expected_notes = {
            None: (NOTE_PER_CHILD_DIFFERENT_SHARES, NOTE_PER_CHILD_DIFFERENT),
            "no": (NOTE_PER_CHILD_DIFFERENT, NOTE_PER_CHILD_DIFFERENT_SHARES),
        }
        for flag, (present, absent) in expected_notes.items():
            with self.subTest(flag=flag):
                result = compute(*P1, ["30", "40"], 2, WAGE, flag)
                self.assertIsNone(allocation(result))
                text = render_report(result)
                self.assertEqual(text.count(present), 1)
                self.assertNotIn(absent, text)
                self.assertNotIn(NOTE_PER_CHILD_NO_FLAG, text)
                self.assertNotIn("Allocation per child (FC 4055(b)(8))", text.split("\n"))
                lines = text.split("\n")
                self.assertEqual(
                    [l for l in lines if l.startswith(support_prefix)], single_support
                )

    def test_allocation_refuses_different_shares_even_if_the_flag_is_on_the_result(self):
        result = compute(*P1, ["30", "40"], 2, WAGE)
        forced = dataclasses.replace(result, same_time_sharing_arrangement="yes")
        self.assertIsNone(allocation(forced))

    def test_different_shares_are_found_whichever_share_is_larger(self):
        for shares in (["40", "30"], ["35", "35", "30"]):
            with self.subTest(shares=shares):
                count = len(shares)
                with self.assertRaises(ValueError) as caught:
                    compute(*P1, shares, count, WAGE, same_time_sharing_arrangement="yes")
                self.assertEqual(str(caught.exception), S_CONTRA)
                result = compute(*P1, shares, count, WAGE)
                self.assertEqual(
                    render_report(result).count(NOTE_PER_CHILD_DIFFERENT_SHARES), 1
                )
                forced = dataclasses.replace(result, same_time_sharing_arrangement="yes")
                self.assertIsNone(allocation(forced))

    def test_different_shares_with_flag_yes_is_an_error_naming_both_inputs(self):
        with self.assertRaises(ValueError) as caught:
            compute(*P1, ["30", "40"], 2, WAGE, same_time_sharing_arrangement="yes")
        self.assertEqual(str(caught.exception), S_CONTRA)
        base = cli_flags("6000.00", "2000.00", ["30", "40"], 2)
        orders = {
            "flag last": base + [FLAG, "yes"],
            "flag first": [FLAG, "yes"] + base,
        }
        for name, args in orders.items():
            with self.subTest(order=name):
                done = run_cli(*args)
                self.assertEqual(done.returncode, 2)
                self.assertEqual(done.stdout, "")
                self.assertEqual(len(done.stderr.splitlines()), 1)
                self.assertEqual(done.stderr.splitlines()[0], S_CONTRA_CLI)
                self.assertIn("--a-time-percent", done.stderr)
                self.assertIn(FLAG, done.stderr)
                prefix = "python3 -m family_law_toolkit.support: error: "
                self.assertNotIn("_", done.stderr[len(prefix):])

    def test_equal_shares_without_the_flag_behave_as_today(self):
        for flag, note in ((None, NOTE_PER_CHILD_NO_FLAG), ("no", NOTE_PER_CHILD_DIFFERENT)):
            with self.subTest(flag=flag):
                listed = compute(*P1, ["35", "35"], 2, WAGE, flag)
                single = compute(*P1, "35", 2, WAGE, flag)
                self.assertIsNone(allocation(listed))
                self.assertIsNone(allocation(single))
                list_text = render_report(listed)
                self.assertEqual(list_text.count(note), 1)
                self.assertEqual(normalise_list_report(list_text), render_report(single))

    def test_equal_shares_with_the_flag_allocate(self):
        pairs = ((P1, ["35", "35", "35"], "35"), (LIA, ["25", "25", "25"], "25"))
        for index, (money_pair, shares, single_share) in enumerate(pairs):
            with self.subTest(case=index):
                listed = compute(*money_pair, shares, 3, WAGE, "yes")
                single = compute(*money_pair, single_share, 3, WAGE, "yes")
                self.assertIsNotNone(allocation(listed))
                self.assertEqual(allocation(listed), allocation(single))
                if index == 1:
                    self.assertIsNotNone(allocation(listed).bottom)
                self.assertEqual(
                    normalise_list_report(render_report(listed)), render_report(single)
                )

    def test_equal_shares_written_differently_count_as_equal(self):
        shares = ["35", "35.0", "35.00"]
        # (a) flag yes: parsed values are equal, so no contradiction error.
        listed = compute(*P1, shares, 3, WAGE, "yes")
        single = compute(*P1, "35", 3, WAGE, "yes")
        self.assertIsNotNone(allocation(listed))
        self.assertEqual(allocation(listed), allocation(single))
        text = render_report(listed)
        self.assertNotIn(NOTE_PER_CHILD_DIFFERENT, text)
        self.assertNotIn(NOTE_PER_CHILD_DIFFERENT_SHARES, text)
        self.assertIn(
            "  Parent A's share of time, by child: 35%, 35%, 35%", text.split("\n")
        )
        # (b) flag omitted: same as equal shares today.
        omitted = compute(*P1, shares, 3, WAGE)
        omitted_text = render_report(omitted)
        self.assertEqual(omitted_text.count(NOTE_PER_CHILD_NO_FLAG), 1)
        self.assertNotIn(NOTE_PER_CHILD_DIFFERENT, omitted_text)
        self.assertNotIn(NOTE_PER_CHILD_DIFFERENT_SHARES, omitted_text)
        # (c) the flag set on that result still allocates.
        self.assertIsNotNone(
            allocation(dataclasses.replace(omitted, same_time_sharing_arrangement="yes"))
        )

    def test_single_share_path_is_unchanged(self):
        cases = []
        for name in ("guideline_step1.json", "guideline_step2.json"):
            with (ROOT / "tests" / "golden" / name).open(encoding="utf-8") as handle:
                cases += json.load(handle)["cases"]
        self.assertTrue(cases)
        for case in cases:
            with self.subTest(case=case["id"]):
                i = case["inputs"]
                result = compute(
                    i["a_ndi"], i["b_ndi"], i["a_time_percent"], i["children"],
                    i["minimum_wage_hourly"], i.get("same_time_sharing_arrangement"),
                )
                self.assertIsNone(result.a_time_percent_by_child)
                text = render_report(result)
                self.assertNotIn(", by child:", text)
                self.assertNotIn(report.READING_AVERAGE_LINE, text)
        g1 = next(case for case in cases if case["id"] == "G1")["inputs"]
        done = run_cli(*cli_flags(
            g1["a_ndi"], g1["b_ndi"], [g1["a_time_percent"]], g1["children"],
            g1["minimum_wage_hourly"],
        ))
        expected = render_report(compute(
            g1["a_ndi"], g1["b_ndi"], g1["a_time_percent"], g1["children"],
            g1["minimum_wage_hourly"],
        )) + "\n"
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout, expected)

    def test_share_count_must_match_children(self):
        for shares, children in ((["30", "40", "50"], 2), (["30", "40"], 1), ([], 1)):
            with self.subTest(shares=shares, children=children):
                with self.assertRaises(ValueError) as caught:
                    compute(*P1, shares, children, WAGE)
                self.assertEqual(str(caught.exception), S_COUNT)
        done = run_cli(*cli_flags("6000.00", "2000.00", ["30", "40", "50"], 2))
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stderr.splitlines(), [S_COUNT_CLI])

    def test_each_share_gets_the_existing_checks(self):
        with self.assertRaises(ValueError) as caught:
            compute(*P1, ["30", "100.01"], 2, WAGE)
        self.assertEqual(str(caught.exception), "a_time_percent must be between 0 and 100")
        with self.assertRaises(ValueError) as caught:
            compute(*P1, ["30", 40], 2, WAGE)
        self.assertEqual(str(caught.exception), "a_time_percent must be a decimal string")
        self.assertEqual(
            compute(*P1, ("30", "40"), 2, WAGE).h_percent,
            compute(*P1, ["30", "40"], 2, WAGE).h_percent,
        )
        done = run_cli(*cli_flags("6000.00", "2000.00", ["30,40"], 2))
        self.assertEqual(done.returncode, 2)
        self.assertEqual(
            done.stderr.splitlines(),
            ["python3 -m family_law_toolkit.support: error: "
             "--a-time-percent is not a decimal number"],
        )

    def test_cli_repeated_flag_gives_one_share_per_child(self):
        done = run_cli(*cli_flags("6000.00", "2000.00", ["30", "40"], 2))
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stderr, "")
        expected = render_report(compute("6000.00", "2000.00", ["30", "40"], 2, WAGE)) + "\n"
        self.assertEqual(done.stdout, expected)

    def test_help_explains_repeating_the_flag(self):
        done = run_cli("--help")
        self.assertEqual(done.returncode, 0)
        collapsed = re.sub(r"\s+", " ", done.stdout)
        self.assertIn(S_HELP, collapsed)


def normalise_list_report(text):
    """Make a per-child report of equal shares read like the single-share one.

    (a) the by-child echo becomes the single-share echo; (b) the one
    READING_AVERAGE_LINE line is deleted.
    """
    out = []
    for line in text.split("\n"):
        if line == S_READ:
            continue
        match = re.match(r"^  Parent A's share of time, by child: (\d+)%(?:, \1%)*$", line)
        if match:
            line = "  Parent A's share of time: %s%%" % match.group(1)
        out.append(line)
    return "\n".join(out)


if __name__ == "__main__":
    unittest.main()
