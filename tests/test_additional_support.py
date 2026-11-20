# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Tests for the additional child support section of the support command
(docs/specs/add-ons.md, with its hand derivations in docs/derivations/add-ons.md).

The expected values here come from the spec's fixture table and from an oracle
below that uses fractions.Fraction only. It does not import family_law_toolkit
to work out an expected value.
"""

import re
import unittest
from fractions import Fraction as F
from types import SimpleNamespace

from family_law_toolkit.support import additional
from family_law_toolkit.support.report import (
    CLOSING_LINE,
    IDENTITY_LINE,
    NOTE_NDI,
    NOTE_TIME_SHARE,
)
from tests.test_report import run_cli

# ---------------------------------------------------------------------------
# The oracle: FC 4055 for one child, and the FC 4061 split. Fractions only.
# ---------------------------------------------------------------------------

ROWS = (
    (F(2900), F("0.165"), F(1, 82857), F(0)),
    (F(5000), F("0.131"), F(1, 42149), F(0)),
    (F(10000), F("0.25"), F(0), F(0)),
    (F(15000), F("0.10"), F(0), F(1499)),
    (None, F("0.12"), F(0), F(1200)),
)


def cents(x):
    """Half up to whole cents, from a non-negative exact value in dollars."""
    return int((x * 100 + F(1, 2)) // 1)


def text_of(x):
    """Dollars and cents of an exact value that is already a whole number of
    cents, with a leading minus when negative."""
    c = int(x * 100)
    return ("-" if c < 0 else "") + "%d.%02d" % divmod(abs(c), 100)


def cents_text(c):
    return "%d.%02d" % divmod(c, 100)


def basic(a, b, a_time, wage="21.00"):
    """One child. Returns (payer, support, low) with low None when no range."""
    a, b, a_time, wage = F(a), F(b), F(a_time), F(wage)
    tn = a + b
    if a >= b:
        high, hn, h = "A", a, a_time / 100
    else:
        high, hn, h = "B", b, 1 - a_time / 100
    for upper, const, ctn, cinv in ROWS:
        if upper is None or tn <= upper:
            frac = const + ctn * tn + (cinv / tn if cinv else 0)
            break
    k = (1 + h if h <= F(1, 2) else 2 - h) * frac
    cs = k * (hn - h * tn)
    if cs > 0:
        payer = high
    elif cs < 0:
        payer = "B" if high == "A" else "A"
    else:
        payer = "none"
    support = abs(cs)
    threshold = wage * 40 * 52 / 12
    ndi = {"A": a, "B": b}.get(payer)
    low = None
    if ndi is not None and ndi < threshold:
        low = support - support * (threshold - ndi) / threshold
    return payer, support, low


def end_split(payer, support_cents, a_adj, b_adj, total):
    """The FC 4061(d) reduction by the printed support, then the split.
    Returns (a_cents, b_cents, a_hundredths, b_hundredths, ra, rb)."""
    a_adj, b_adj, total = F(a_adj), F(b_adj), F(total)
    ra, rb = a_adj, b_adj
    if payer == "A":
        ra = a_adj - F(support_cents, 100)
    elif payer == "B":
        rb = b_adj - F(support_cents, 100)
    a = cents(total * ra / (ra + rb))
    ah = cents(ra / (ra + rb) * 100)
    return (a, int(total * 100) - a, ah, 10000 - ah, ra, rb)


# ---------------------------------------------------------------------------
# Printed strings, written out here (not imported), so a change to the report
# text is a change a reader sees in this file.
# ---------------------------------------------------------------------------

SUFFIX = " Run with --help to see what each flag means."
E3 = (
    "If no spousal support is or has been ordered, enter the same figures you "
    "gave for `--a-ndi` and `--b-ndi`."
)
REST_HEADING = "Additional child support (FC 4062)"
REST_TEXT = (
    "  No additional child support costs were entered. "
    "This report does not say that none apply."
)
HEADING = "Additional child support (FC 4062), split under FC 4061"
CHILDCARE_LABEL = (
    "    Childcare costs related to employment or to reasonably necessary "
    "education or training for employment skills (FC 4062(a)(1)): "
)
HEALTH_LABEL = (
    "    The reasonable uninsured health care costs for the children "
    "(FC 4062(a)(2)): "
)
REDUCTION_HEADING = (
    "  Basic support is taken first (FC 4061(b)(1)); then the paying parent's "
    "figure is reduced by it (FC 4061(d)):"
)
SPLIT_HEADING = "  Split in proportion to those figures (FC 4061(a), (b)(2)):"
N1 = (
    "You enter each parent's adjusted net disposable income yourself. "
    "This report does not adjust income for spousal support (FC 4061(c))."
)
N2 = (
    "Costs the court may order (FC 4062(b)) are not computed here, and nothing "
    "in this report shows them as owed."
)
N3 = (
    "This report does not decide which costs count, whether a cost is actually "
    "incurred or reasonable, or whether a cost is already included in the "
    "guideline figure. For those questions you can ask a lawyer, your court's "
    "self-help center, or its family law facilitator."
)
N4 = (
    "The basic support amount above is this report's own arithmetic. It does "
    "not apply the rebuttal factors of FC 4057 (see FC 4061(b)(1)), and FC "
    "4061(d) reduces by the basic support \"ordered to be paid\", which can "
    "differ from this figure."
)
REFERRAL = (
    "For help working out the figures for your own case, you can ask a lawyer, "
    "your court's self-help center, or its family law facilitator."
)
ROW7_REFERRAL = (
    "For help with these figures you can ask a lawyer, your court's "
    "self-help center, or its family law facilitator."
)
ZERO_SUPPORT_LINE = (
    "    Basic support prints 0.00, so the reduction is 0.00 and both figures "
    "stay as typed (FC 4061(d))."
)
STATUTE_CHILDCARE = (
    "Childcare costs, if those expenses are actually incurred, related to "
    "employment or to reasonably necessary education or training for "
    "employment skills, as described in Section 4063, unless those costs are "
    "specifically included in the guideline calculation itself."
)
STATUTE_HEALTH = (
    "The reasonable uninsured health care costs for the children as provided "
    "in Section 4063."
)


def guideline(a, b, t, wage="21.00", children="1"):
    return ("--a-ndi", a, "--b-ndi", b, "--a-time-percent", t,
            "--children", children, "--minimum-wage-hourly", wage)


AO1 = guideline("5000.00", "3000.00", "20")
AO2 = guideline("6000.00", "2000.00", "10")
AO3 = guideline("4000.00", "8000.00", "30")
AO4 = guideline("3000.00", "1000.00", "0")


def costs(childcare=None, health=None):
    out = ()
    if childcare is not None:
        out += ("--childcare-monthly", childcare)
    if health is not None:
        out += ("--uninsured-health-monthly", health)
    return out


def adjusted(a, b):
    return ("--a-adjusted-ndi", a, "--b-adjusted-ndi", b)


def ok(*args):
    done = run_cli(*args)
    assert done.returncode == 0, done.stderr
    assert done.stderr == "", done.stderr
    return done.stdout.split("\n")


def proportional_lines(payer, support_cents, a_typed, b_typed, total):
    """The oracle's expected lines under the reduction heading and the split
    heading, for one end, with the heading lines themselves."""
    a_cents, b_cents, ah, bh, ra, rb = end_split(
        payer, support_cents, a_typed, b_typed, total
    )
    s = cents_text(support_cents)
    if payer == "A":
        first = "    Parent A, the paying parent in this report: %s - %s = %s" % (
            text_of(F(a_typed)), s, text_of(ra))
        second = "    Parent B is not increased by support received: %s" % text_of(rb)
    else:
        first = "    Parent B, the paying parent in this report: %s - %s = %s" % (
            text_of(F(b_typed)), s, text_of(rb))
        second = "    Parent A is not increased by support received: %s" % text_of(ra)
    den = text_of(ra + rb)
    return [
        REDUCTION_HEADING, first, second, SPLIT_HEADING,
        "    Parent A: %s / %s = %s%%: %s" % (text_of(ra), den, cents_text(ah), cents_text(a_cents)),
        "    Parent B: %s / %s = %s%%: %s" % (text_of(rb), den, cents_text(bh), cents_text(b_cents)),
    ], (a_cents, b_cents)


def assert_contiguous(testcase, lines, expected):
    """expected appears in lines, in order, with no line between."""
    testcase.assertIn(expected[0], lines)
    start = lines.index(expected[0])
    testcase.assertEqual(lines[start:start + len(expected)], expected)


class AdditionalSupportTests(unittest.TestCase):
    # -- the fixtures of the spec, AO1 to AO5, each with its oracle ----------

    def test_ao1_default_split_payer_a(self):
        out = ok(*AO1, *costs("600.00", "120.00"), *adjusted("5000.00", "3000.00"))
        expected = [
            HEADING,
            "  Costs you entered, monthly:",
            CHILDCARE_LABEL + "600.00",
            HEALTH_LABEL + "120.00",
            "    Total: 720.00",
            "  Net disposable income figures used (you entered them; this report did not adjust them):",
            "    Parent A, as you entered it: 5000.00",
            "    Parent B, as you entered it: 3000.00",
            REDUCTION_HEADING,
            "    Parent A, the paying parent in this report: 5000.00 - 1020.00 = 3980.00",
            "    Parent B is not increased by support received: 3000.00",
            SPLIT_HEADING,
            "    Parent A: 3980.00 / 6980.00 = 57.02%: 410.54",
            "    Parent B: 3000.00 / 6980.00 = 42.98%: 309.46",
        ]
        assert_contiguous(self, out, expected)
        # The oracle, recomputed from scratch, agrees with the spec's table.
        payer, support, low = basic("5000.00", "3000.00", "20")
        self.assertEqual((payer, support, low), ("A", F(1020), None))
        lines, amounts = proportional_lines(payer, cents(support), "5000.00", "3000.00", "720.00")
        self.assertEqual(amounts, (41054, 30946))
        self.assertEqual(lines, expected[8:])

    def test_ao2_typed_adjusted_figures_differ_from_the_ndis(self):
        out = ok(*AO2, *costs("450.00"), *adjusted("5400.00", "2600.00"))
        payer, support, low = basic("6000.00", "2000.00", "10")
        self.assertEqual((payer, support, low), ("A", F(1430), None))
        lines, amounts = proportional_lines(payer, cents(support), "5400.00", "2600.00", "450.00")
        self.assertEqual(amounts, (27192, 17808))
        assert_contiguous(self, out, lines)
        self.assertIn("    Parent A, the paying parent in this report: 5400.00 - 1430.00 = 3970.00", out)
        self.assertIn("    Parent A: 3970.00 / 6570.00 = 60.43%: 271.92", out)
        self.assertIn("    Parent B: 2600.00 / 6570.00 = 39.57%: 178.08", out)
        self.assertIn("    Total: 450.00", out)

    def test_ao3_payer_is_not_the_high_earner(self):
        out = ok(*AO3, *costs("500.00"), *adjusted("4000.00", "8000.00"))
        payer, support, low = basic("4000.00", "8000.00", "30")
        self.assertEqual(payer, "A")
        self.assertEqual(cents(support), 11696)
        self.assertIsNone(low)
        lines, amounts = proportional_lines(payer, cents(support), "4000.00", "8000.00", "500.00")
        self.assertEqual(amounts, (16339, 33661))
        assert_contiguous(self, out, lines)
        self.assertIn("    Parent A, the paying parent in this report: 4000.00 - 116.96 = 3883.04", out)
        self.assertIn("    Parent A: 3883.04 / 11883.04 = 32.68%: 163.39", out)
        self.assertIn("    Parent B: 8000.00 / 11883.04 = 67.32%: 336.61", out)

    def test_ao4_range_prints_both_ends(self):
        out = ok(*AO4, *costs("300.00"), *adjusted("3000.00", "1000.00"))
        payer, support, low = basic("3000.00", "1000.00", "0")
        self.assertEqual(payer, "A")
        self.assertEqual((cents(low), cents(support)), (55855, 67770))
        top, top_amounts = proportional_lines(payer, cents(support), "3000.00", "1000.00", "300.00")
        bottom, bottom_amounts = proportional_lines(payer, cents(low), "3000.00", "1000.00", "300.00")
        self.assertEqual(top_amounts, (20970, 9030))
        self.assertEqual(bottom_amounts, (21283, 8717))
        expected = (
            ["  At the top of the support range, 677.70:"] + top
            + ["  At the bottom of the support range, 558.55:"] + bottom
        )
        assert_contiguous(self, out, expected)
        # The cost and income blocks print once, before the two ends.
        self.assertEqual(out.count("    Total: 300.00"), 1)
        self.assertEqual(out.count("    Parent A, as you entered it: 3000.00"), 1)
        self.assertLess(out.index("    Parent A, as you entered it: 3000.00"),
                        out.index("  At the top of the support range, 677.70:"))

    def test_ao5_cost_share_split_has_no_proportional_lines(self):
        out = ok(*AO1, *costs("600.00", "120.00"), "--a-cost-share-percent", "50")
        expected = [
            HEADING,
            "  Costs you entered, monthly:",
            CHILDCARE_LABEL + "600.00",
            HEALTH_LABEL + "120.00",
            "    Total: 720.00",
            "  Split you entered: Parent A 50%, Parent B 50%",
            "    Parent A: 360.00",
            "    Parent B: 360.00",
        ]
        assert_contiguous(self, out, expected)
        self.assertEqual(F("720.00") * F(50, 100), 360)
        self.assertNotIn(SPLIT_HEADING, out)
        self.assertNotIn(REDUCTION_HEADING, out)
        self.assertFalse(any("Net disposable income figures used" in l for l in out))

    def test_ao6_rest_state(self):
        out = ok(*AO1)
        self.assertEqual(out.count(REST_HEADING), 1)
        at = out.index(REST_HEADING)
        self.assertEqual(out[at + 1], REST_TEXT)
        self.assertEqual(out[at - 1], "")
        self.assertEqual(out[at + 2], "")
        self.assertEqual(out[at + 3], NOTE_NDI)
        # It follows the low-income lines.
        self.assertTrue(out[at - 2].startswith("  The paying parent's net disposable income is not less"))
        for note in (N1, N2, N3, N4):
            self.assertNotIn(note, out)
        self.assertFalse(any("(FC 4062" in l and "split" in l for l in out))

    # -- AO7: the refusals, rows 1 to 7 and row 9 (a build addition) --------------------

    def assert_refused(self, args, message):
        done = run_cli(*args)
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertEqual(done.stdout, "")
        self.assertEqual(done.stderr.count("\n"), 1, done.stderr)
        line = done.stderr.rstrip("\n")
        self.assertTrue(line.endswith(SUFFIX), line)
        self.assertEqual(
            line, "python3 -m family_law_toolkit.support: error: " + message + SUFFIX
        )
        return line

    def test_ao7_row1_a_value_that_is_not_a_plain_number(self):
        self.assert_refused(
            (*AO1, "--childcare-monthly", "abc", *adjusted("5000.00", "3000.00")),
            "--childcare-monthly is not a decimal number.")
        self.assert_refused(
            (*AO1, "--uninsured-health-monthly", "1.234", *adjusted("5000.00", "3000.00")),
            "--uninsured-health-monthly has more than 2 decimals.")
        self.assert_refused(
            (*AO1, *costs("10.00"), "--a-adjusted-ndi", "-1", "--b-adjusted-ndi", "5.00"),
            "--a-adjusted-ndi must not be negative.")
        self.assert_refused(
            (*AO1, *costs("10.00"), "--a-cost-share-percent", "x"),
            "--a-cost-share-percent is not a decimal number.")

    def test_ao7_row1_a_negative_cost(self):
        self.assert_refused(
            (*AO1, "--childcare-monthly", "-0.01", "--a-cost-share-percent", "50"),
            "--childcare-monthly must not be negative.")

    def test_ao7_row2_a_cost_with_no_way_to_split_it(self):
        line = self.assert_refused(
            (*AO1, *costs("600.00")),
            "A cost was entered without a way to split it: give "
            "--a-cost-share-percent, or give both --a-adjusted-ndi and "
            "--b-adjusted-ndi. " + E3)
        self.assertIn(E3 + SUFFIX, line)
        self.assertIn(E3 + SUFFIX, self.assert_refused(
            (*AO1, *costs(None, "10.00")),
            "A cost was entered without a way to split it: give "
            "--a-cost-share-percent, or give both --a-adjusted-ndi and "
            "--b-adjusted-ndi. " + E3))

    def test_ao7_row3_only_one_adjusted_figure(self):
        line = self.assert_refused(
            (*AO1, *costs("600.00"), "--a-adjusted-ndi", "5000.00"),
            "Only --a-adjusted-ndi was given, and this report needs both "
            "--a-adjusted-ndi and --b-adjusted-ndi. " + E3)
        self.assertIn(E3 + SUFFIX, line)
        self.assert_refused(
            (*AO1, *costs("600.00"), "--b-adjusted-ndi", "3000.00"),
            "Only --b-adjusted-ndi was given, and this report needs both "
            "--a-adjusted-ndi and --b-adjusted-ndi. " + E3)

    def test_ao7_row4_adjusted_figures_with_no_cost(self):
        self.assert_refused(
            (*AO1, *adjusted("5000.00", "3000.00")),
            "--a-adjusted-ndi and --b-adjusted-ndi were given with no cost, so "
            "they would go unused. Give --childcare-monthly or "
            "--uninsured-health-monthly, or leave them out.")

    def test_ao7_row5_a_share_together_with_adjusted_figures(self):
        message = (
            "--a-cost-share-percent was given together with an adjusted-income "
            "option, so it is unclear which split to use. Give one or the other.")
        self.assert_refused(
            (*AO1, *costs("600.00"), "--a-cost-share-percent", "50",
             *adjusted("5000.00", "3000.00")), message)
        # One adjusted figure beside a share is also this message, not row 3.
        self.assert_refused(
            (*AO1, *costs("600.00"), "--a-cost-share-percent", "50",
             "--a-adjusted-ndi", "5000.00"), message)

    def test_ao7_row6_a_share_out_of_range_or_an_option_repeated(self):
        self.assert_refused(
            (*AO1, *costs("600.00"), "--a-cost-share-percent", "100.01"),
            "--a-cost-share-percent must be between 0 and 100.")
        self.assert_refused(
            (*AO1, *costs("600.00"), "--a-cost-share-percent", "-1"),
            "--a-cost-share-percent must be between 0 and 100.")
        self.assert_refused(
            (*AO1, "--childcare-monthly", "1.00", "--childcare-monthly", "2.00",
             "--a-cost-share-percent", "50"),
            "--childcare-monthly was given more than once.")
        self.assert_refused(
            (*AO1, *costs("1.00"), "--a-cost-share-percent", "50",
             "--a-cost-share-percent", "60"),
            "--a-cost-share-percent was given more than once.")

    def test_ao7_row7_a_reduced_figure_below_zero(self):
        # AO2's guideline inputs: basic support 1430.00 paid by A.
        # Typed A 1000.00 less 1430.00 is -430.00; B is 2600.00.
        self.assert_refused(
            (*AO2, *costs("450.00"), *adjusted("1000.00", "2600.00")),
            "After FC 4061(d) takes basic support from the paying parent's figure, "
            "the figures are Parent A: -430.00 and Parent B: 2600.00, and a share "
            "cannot be worked out from them. " + ROW7_REFERRAL)

    def test_ao7_row9_a_share_with_no_cost(self):
        # A build addition: the spec's table has no row for this.
        self.assert_refused(
            (*AO1, "--a-cost-share-percent", "50"),
            "--a-cost-share-percent was given with no cost, so it would go unused. "
            "Give --childcare-monthly or --uninsured-health-monthly, or leave it out.")

    def test_ao7_the_help_pointer_ends_a_refusal_for_every_row(self):
        done = run_cli(*AO1, *costs("600.00"))
        self.assertEqual(done.returncode, 2)
        # Row 2 puts E3 immediately before the pointer.
        self.assertIn(E3 + SUFFIX + "\n", done.stderr)

    # -- build additions: payer B, payer none, row 7 and its scope ------------

    # AO8, payer B (derived by hand, python3 -I -c with Fractions):
    #   k=(1+3/10)*1/4 -> 13/40; x=k*(6000-3/10*8000) -> 1170 -> 1170.00
    #   a=540*2000/(2000+4830) -> 108000/683 = 158.13 ; B = 540 - 158.13 = 381.87
    #   2000/6830 -> 29.28% (A), 4830/6830 -> 70.72% (B); 29.28 + 70.72 = 100.00
    def test_ao8_payer_b_mirrors_the_lines(self):
        guide = guideline("2000.00", "6000.00", "70")
        out = ok(*guide, *costs("450.00", "90.00"), *adjusted("2000.00", "6000.00"))
        payer, support, low = basic("2000.00", "6000.00", "70")
        self.assertEqual((payer, support, low), ("B", F(1170), None))
        lines, amounts = proportional_lines("B", 117000, "2000.00", "6000.00", "540.00")
        self.assertEqual(amounts, (15813, 38187))
        assert_contiguous(self, out, lines)
        self.assertIn("    Parent B, the paying parent in this report: 6000.00 - 1170.00 = 4830.00", out)
        self.assertIn("    Parent A is not increased by support received: 2000.00", out)
        self.assertIn("    Parent A: 2000.00 / 6830.00 = 29.28%: 158.13", out)
        self.assertIn("    Parent B: 4830.00 / 6830.00 = 70.72%: 381.87", out)
        self.assertFalse(any("Parent A, the paying parent" in l for l in out))

    # AO9, no paying parent (python3 -I -c with Fractions):
    #   a=300*2000/(2000+1000) -> 200 -> 200.00 ; B = 300 - 200 = 100.00
    #   2/3*100 -> 66.666... : A 66.67%, B = 100.00 - 66.67 = 33.33%
    def test_ao9_no_paying_parent_both_figures_stay_as_typed(self):
        guide = guideline("0", "0", "50")
        out = ok(*guide, *costs("300.00"), *adjusted("2000.00", "1000.00"))
        self.assertIn("  Paying parent (FC 4055(b)(5)): none", out)
        expected = [
            REDUCTION_HEADING,
            ZERO_SUPPORT_LINE,
            SPLIT_HEADING,
            "    Parent A: 2000.00 / 3000.00 = 66.67%: 200.00",
            "    Parent B: 1000.00 / 3000.00 = 33.33%: 100.00",
        ]
        assert_contiguous(self, out, expected)
        self.assertFalse(any("paying parent in this report" in l for l in out))

    # Row 7 and its scope, on AO2's guideline inputs (basic support 1430.00, A pays):
    #   typed A 1000.00 -> 1000.00 - 1430.00 = -430.00 (refused)
    #   typed A 1430.00, B 0.00 -> 0.00 and 0.00 (sum not above zero: refused)
    #   typed A 1430.00, B 2600.00 -> 0.00 and 2600.00 (not refused; A 0%, B 100%)
    def test_row7_refuses_when_the_sum_is_not_above_zero(self):
        self.assert_refused(
            (*AO2, *costs("450.00"), *adjusted("1430.00", "0.00")),
            "After FC 4061(d) takes basic support from the paying parent's figure, "
            "the figures are Parent A: 0.00 and Parent B: 0.00, and a share "
            "cannot be worked out from them. " + ROW7_REFERRAL)

    def test_row7_does_not_refuse_a_reduced_figure_of_exactly_zero_beside_a_positive_one(self):
        out = ok(*AO2, *costs("450.00"), *adjusted("1430.00", "2600.00"))
        expected = [
            REDUCTION_HEADING,
            "    Parent A, the paying parent in this report: 1430.00 - 1430.00 = 0.00",
            "    Parent B is not increased by support received: 2600.00",
            SPLIT_HEADING,
            "    Parent A: 0.00 / 2600.00 = 0.00%: 0.00",
            "    Parent B: 2600.00 / 2600.00 = 100.00%: 450.00",
        ]
        assert_contiguous(self, out, expected)

    def test_row7_in_a_range_tests_the_top_end_first(self):
        # AO4's inputs: top 677.70, bottom 558.55. A typed 600.00: 600 - 677.70 = -77.70
        # at the top. The bottom end (600 - 558.55 = 41.45) would pass by itself, but
        # the reduction is monotone in the support amount, so a failure at the bottom
        # always fails at the top first: no input fails at the bottom alone.
        self.assert_refused(
            (*AO4, *costs("300.00"), *adjusted("600.00", "0.00")),
            "At the top of the support range (support 677.70): After FC 4061(d) "
            "takes basic support from the paying parent's figure, the figures are "
            "Parent A: -77.70 and Parent B: 0.00, and a share cannot be worked "
            "out from them. " + ROW7_REFERRAL)

    def test_row7_bottom_end_message_carries_its_own_prefix(self):
        # The bottom end cannot fail alone from the command (see the test above), so
        # this drives the function that builds one end.
        stand_in = SimpleNamespace(payer="A")
        with self.assertRaises(additional.AdditionalSupportRefused) as raised:
            additional._end(stand_in, "bottom", 5855, F(10), F(0), 30000, True)
        self.assertTrue(str(raised.exception).startswith(
            "At the bottom of the support range (support 58.55): After FC 4061(d)"))

    # -- rounding -------------------------------------------------------------

    # python3 -I -c with Fractions: a=0.01*50/100 -> 1/200 (0.5 of a cent) -> 0.01 half up;
    #   B = 0.01 - 0.01 = 0.00 (B rounded on its own, 1/200, would also be 0.01).
    def test_cost_share_half_cent_rounds_up_and_b_is_the_rest(self):
        out = ok(*AO1, *costs("0.01"), "--a-cost-share-percent", "50")
        self.assertIn("    Parent A: 0.01", out)
        self.assertIn("    Parent B: 0.00", out)
        self.assertIn("    Total: 0.01", out)

    # python3 -I -c: a=0.03*50/100 -> 3/200 = 0.015 -> 0.02 half up; B = 0.03 - 0.02 = 0.01.
    def test_cost_share_a_second_tie_total_minus_a(self):
        out = ok(*AO1, *costs("0.03"), "--a-cost-share-percent", "50")
        self.assertIn("    Parent A: 0.02", out)
        self.assertIn("    Parent B: 0.01", out)

    def test_cost_share_asymmetric_split_is_not_swapped(self):
        # python3 -I -c: 720.00*30/100 -> 216 -> A 216.00, B 504.00
        out = ok(*AO1, *costs("600.00", "120.00"), "--a-cost-share-percent", "30")
        self.assertIn("  Split you entered: Parent A 30%, Parent B 70%", out)
        self.assertIn("    Parent A: 216.00", out)
        self.assertIn("    Parent B: 504.00", out)

    def test_cost_share_percent_prints_without_trailing_zeros_and_keeps_two_decimals(self):
        out = ok(*AO1, *costs("100.00"), "--a-cost-share-percent", "33.33")
        self.assertIn("  Split you entered: Parent A 33.33%, Parent B 66.67%", out)
        self.assertIn("    Parent A: 33.33", out)
        self.assertIn("    Parent B: 66.67", out)

    def test_proportional_amounts_add_to_the_total_over_a_sweep(self):
        # 2000 invented inputs were searched (random, fixed seed, scratch script) for a
        # case where B rounded on its own differs from total minus A; none exists, so
        # the half-cent fixtures above are what pin "B is the rest". Here the sum.
        for a, b, t, cost in (("8240.00", "5606.00", "10", "876.42"),
                              ("7568.00", "4423.00", "40", "506.59"),
                              ("1417.00", "1285.00", "60", "485.48")):
            with self.subTest(a=a, b=b):
                out = ok(*guideline(a, b, t), *costs(cost), *adjusted(a, b))
                lines = [l for l in out if re.match(r"    Parent [AB]: .* = .*%: ", l)]
                # Two lines per end; a low-income range has two ends.
                self.assertEqual(len(lines) % 2, 0)
                for i in range(0, len(lines), 2):
                    pair = lines[i:i + 2]
                    shown = [F(l.rsplit(": ", 1)[1]) for l in pair]
                    self.assertEqual(shown[0] + shown[1], F(cost))
                    percents = [F(re.search(r"= ([0-9.]+)%", l).group(1)) for l in pair]
                    self.assertEqual(sum(percents), 100)

    # Printed vs exact support (O3), found by a search of 5000 invented inputs:
    #   A 8240.00, B 5606.00, A's time 10, childcare 876.42, adjusted typed as the NDIs.
    #   r=0.10+1499/13846 -> 7209/34615 ; k=(1+1/10)*r ; x=k*(8240-1/10*13846)
    #   -> 2718131823/1730750 = 1570.4936... -> printed 1570.49
    #   reduce by the printed 1570.49 : A 476.18, B 400.24
    #   reduce by the exact value     : A 476.17, B 400.25  (differs by one cent)
    def test_o3_the_reduction_uses_the_printed_support_not_the_exact_value(self):
        out = ok(*guideline("8240.00", "5606.00", "10"), *costs("876.42"),
                 *adjusted("8240.00", "5606.00"))
        payer, support, low = basic("8240.00", "5606.00", "10")
        self.assertEqual(cents(support), 157049)
        self.assertNotEqual(support, F(157049, 100))
        lines, amounts = proportional_lines(payer, cents(support), "8240.00", "5606.00", "876.42")
        self.assertEqual(amounts, (47618, 40024))
        assert_contiguous(self, out, lines)
        self.assertIn("    Parent A: 6669.51 / 12275.51 = 54.33%: 476.18", out)
        self.assertIn("    Parent B: 5606.00 / 12275.51 = 45.67%: 400.24", out)

    # -- notes, omitted costs, ranges with a share, words, pagination ----------

    def test_notes_print_only_with_a_cost_and_in_order(self):
        with_adjusted = ok(*AO1, *costs("600.00", "120.00"), *adjusted("5000.00", "3000.00"))
        for note in (N1, N2, N3, N4):
            self.assertEqual(with_adjusted.count(note), 1)
        order = [with_adjusted.index(n) for n in (NOTE_NDI, NOTE_TIME_SHARE, N1, N2, N3, N4)]
        self.assertEqual(order, sorted(order))
        closing = with_adjusted.index(CLOSING_LINE)
        self.assertEqual(with_adjusted[closing - 1], "")
        self.assertEqual(with_adjusted[closing - 2], N4)
        with_share = ok(*AO1, *costs("600.00"), "--a-cost-share-percent", "50")
        self.assertEqual(with_share.count(N1), 0)
        for note in (N2, N3, N4):
            self.assertEqual(with_share.count(note), 1)
        self.assertEqual(with_share.count(CLOSING_LINE), 1)

    def test_one_omitted_cost_prints_not_entered_and_counts_as_zero(self):
        out = ok(*AO1, *costs(None, "120.00"), *adjusted("5000.00", "3000.00"))
        self.assertIn(CHILDCARE_LABEL + "(not entered)", out)
        self.assertIn(HEALTH_LABEL + "120.00", out)
        self.assertIn("    Total: 120.00", out)
        lines, amounts = proportional_lines("A", 102000, "5000.00", "3000.00", "120.00")
        assert_contiguous(self, out, lines)
        self.assertEqual(amounts, (6842, 5158))
        out = ok(*AO1, *costs("600.00"), "--a-cost-share-percent", "50")
        self.assertIn(HEALTH_LABEL + "(not entered)", out)
        self.assertIn("    Total: 600.00", out)

    def test_both_costs_zero_is_not_refused(self):
        out = ok(*AO1, *costs("0.00", "0"), *adjusted("5000.00", "3000.00"))
        self.assertIn(CHILDCARE_LABEL + "0.00", out)
        self.assertIn(HEALTH_LABEL + "0.00", out)
        self.assertIn("    Total: 0.00", out)
        self.assertIn("    Parent A: 3980.00 / 6980.00 = 57.02%: 0.00", out)
        self.assertIn("    Parent B: 3000.00 / 6980.00 = 42.98%: 0.00", out)

    def test_a_range_with_a_cost_share_prints_the_split_once(self):
        out = ok(*AO4, *costs("300.00"), "--a-cost-share-percent", "40")
        self.assertIn("  Split you entered: Parent A 40%, Parent B 60%", out)
        self.assertEqual(out.count("    Parent A: 120.00"), 1)
        self.assertEqual(out.count("    Parent B: 180.00"), 1)
        self.assertFalse(any(l.startswith("  At the top of the support range,") for l in out))
        self.assertFalse(any(l.startswith("  At the bottom of the support range,") for l in out))
        # The existing low-income range is still printed, once.
        self.assertEqual(sum(1 for l in out if l.startswith("  Support range (FC 4055(c)): 558.55 to 677.70")), 1)

    def test_words_no_internal_name_and_no_barred_claims(self):
        runs = {
            "ao1": run_cli(*AO1, *costs("600.00", "120.00"), *adjusted("5000.00", "3000.00")),
            "ao4": run_cli(*AO4, *costs("300.00"), *adjusted("3000.00", "1000.00")),
            "ao5": run_cli(*AO1, *costs("600.00"), "--a-cost-share-percent", "50"),
            "rest": run_cli(*AO1),
            "row2": run_cli(*AO1, *costs("600.00")),
            "row4": run_cli(*AO1, *adjusted("5000.00", "3000.00")),
            "row9": run_cli(*AO1, "--a-cost-share-percent", "50"),
            "row7": run_cli(*AO2, *costs("450.00"), *adjusted("1000.00", "2600.00")),
            "help": run_cli("--help"),
        }
        for name, done in runs.items():
            for stream in (done.stdout, done.stderr):
                lowered = stream.lower()
                with self.subTest(run=name):
                    for word in ("add-on", "add on", "addon", "add‑on"):
                        self.assertNotIn(word, lowered)
                    for word in ("filing-ready", "validated", "court-ready", "accurate", "certified"):
                        if word == "certified":
                            # The identity line and the help say "not certified".
                            self.assertEqual(lowered.count("certified"),
                                             lowered.count("not certified"))
                        else:
                            self.assertNotIn(word, lowered)
        # The identity line is unchanged and opens the report.
        for name in ("ao1", "ao4", "ao5", "rest"):
            self.assertEqual(runs[name].stdout.split("\n")[0], IDENTITY_LINE)

    def test_help_lists_the_new_options_and_carries_the_statute_sentences(self):
        text = " ".join(run_cli("--help").stdout.split())
        for option in ("--childcare-monthly AMOUNT", "--uninsured-health-monthly AMOUNT",
                       "--a-adjusted-ndi AMOUNT", "--b-adjusted-ndi AMOUNT",
                       "--a-cost-share-percent PERCENT"):
            with self.subTest(option=option):
                self.assertIn(option, text)
        self.assertEqual(text.count(STATUTE_CHILDCARE), 1)
        self.assertEqual(text.count(STATUTE_HEALTH), 1)
        reduction = "Not reduced for child support: this report makes the FC 4061(d) reduction itself."
        self.assertEqual(text.count(reduction), 2)
        self.assertEqual(text.count(E3), 2)
        self.assertEqual(text.count("Additional child support (optional):"), 1)
        self.assertIn("Parent A's net disposable income, after any spousal-support adjustment you worked out.", text)
        self.assertIn("Parent B's net disposable income, after any spousal-support adjustment you worked out.", text)
        self.assertIn("Parent A's share of the additional child support costs, as you choose it.", text)
        self.assertIn(
            "These figures are yours to work out. Cost and income figures are monthly "
            "dollars. Give --a-cost-share-percent, or both --a-adjusted-ndi and "
            "--b-adjusted-ndi, with any cost.", text)
        self.assertEqual(text.count(REFERRAL), 1)
        self.assertIn("Example with costs, with invented numbers:", text)

    def test_help_second_example_is_the_costs_command_and_runs(self):
        # The command is wrapped with shell line continuations so that no help line is
        # longer than the existing example's (see the report): rejoin it to run it.
        help_text = run_cli("--help").stdout
        tail = help_text.split("Example with costs, with invented numbers:\n", 1)[1]
        command = " ".join(l.strip().rstrip("\\").strip() for l in tail.strip().split("\n"))
        self.assertEqual(
            command,
            "python3 -m family_law_toolkit.support --a-ndi 5000.00 --b-ndi 3000.00 "
            "--a-time-percent 20 --children 1 --minimum-wage-hourly 21.00 "
            "--childcare-monthly 600.00 --uninsured-health-monthly 120.00 "
            "--a-adjusted-ndi 5000.00 --b-adjusted-ndi 3000.00",
        )
        out = ok(*command.split()[3:])
        self.assertIn("    Parent A: 3980.00 / 6980.00 = 57.02%: 410.54", out)

    def test_usage_line_names_the_new_options(self):
        usage = run_cli("--help").stdout.split("\n\n", 1)[0]
        for option in ("--childcare-monthly", "--uninsured-health-monthly",
                       "--a-adjusted-ndi", "--b-adjusted-ndi", "--a-cost-share-percent"):
            self.assertIn(option, usage)

    def test_a_two_page_report_keeps_the_identity_line_and_one_closing_line(self):
        done = run_cli(*guideline("3000.00", "1000.00", "0", children="5"),
                       "--same-time-sharing-arrangement", "yes",
                       *costs("300.00"), *adjusted("3000.00", "1000.00"))
        self.assertEqual(done.returncode, 0, done.stderr)
        pages = done.stdout.rstrip("\n").split("\f")
        self.assertGreaterEqual(len(pages), 2)
        for page in pages:
            self.assertEqual(page.split("\n")[0], IDENTITY_LINE)
        self.assertEqual(done.stdout.split("\n").count(CLOSING_LINE), 1)
        self.assertEqual(done.stdout.count(HEADING), 1)

    def test_existing_refusals_are_unchanged(self):
        done = run_cli(*guideline("abc", "3000.00", "20"))
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stdout, "")
        self.assertEqual(
            done.stderr,
            "python3 -m family_law_toolkit.support: error: --a-ndi is not a decimal number\n",
        )


if __name__ == "__main__":
    unittest.main()
