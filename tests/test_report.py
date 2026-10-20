"""Tests for the plain-text report, the identity line and the command line."""

import inspect
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from family_law_toolkit import TOOLKIT_NAME, __version__
from family_law_toolkit.support import __main__ as cli_main
from family_law_toolkit.support import report
from family_law_toolkit.support.guideline import compute, money
from family_law_toolkit.support.report import (
    IDENTITY_LINE,
    LOW_INCOME_HEADING,
    NO_SINGLE_FIGURE_LINE,
    NOTE_TIME_SHARE,
    READING_R2_LINE,
    paginate,
    render_report,
)

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_PATH = ROOT / "tests" / "golden" / "guideline_step1.json"
FORBIDDEN_WORDS = ("filing-ready", "court-ready", "court-grade", "validated", "accurate")


def load_cases():
    with GOLDEN_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)["cases"]


def report_for(case):
    inputs = case["inputs"]
    result = compute(
        inputs["a_ndi"],
        inputs["b_ndi"],
        inputs["a_time_percent"],
        inputs["children"],
        inputs["minimum_wage_hourly"],
    )
    return render_report(result)


def low_income_section(text):
    """Lines from the low-income heading to the next blank line."""
    lines = text.split("\n")
    start = lines.index(LOW_INCOME_HEADING)
    end = start
    while end < len(lines) and lines[end] != "":
        end += 1
    return lines[start:end]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "family_law_toolkit.support", *args],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=60,
    )


def cli_args(case):
    inputs = case["inputs"]
    return (
        "--a-ndi", inputs["a_ndi"], "--b-ndi", inputs["b_ndi"],
        "--a-time-percent", inputs["a_time_percent"],
        "--children", str(inputs["children"]),
        "--minimum-wage-hourly", inputs["minimum_wage_hourly"],
    )


def case_by_id(case_id):
    return next(case for case in load_cases() if case["id"] == case_id)


G1_ARGS = cli_args(case_by_id("G1"))


class ReportTests(unittest.TestCase):
    def test_identity_line_exact(self):
        self.assertEqual(TOOLKIT_NAME, "family-law-toolkit")
        self.assertEqual(__version__, "0.1.0")
        self.assertEqual(
            IDENTITY_LINE,
            "family-law-toolkit v0.1.0 — not certified for court filing; "
            "not affiliated with DissoMaster or XSpouse",
        )

    def test_identity_line_on_every_page(self):
        pages = paginate(["body line %d" % number for number in range(200)])
        self.assertGreaterEqual(len(pages), 4)
        for page in pages:
            lines = page.split("\n")
            self.assertEqual(lines[0], IDENTITY_LINE)
            self.assertEqual(lines[1], "")
            self.assertLessEqual(len(lines), report.PAGE_LINES)

    def test_identity_line_unremovable(self):
        self.assertEqual(len(inspect.signature(render_report).parameters), 1)
        for case in load_cases():
            with self.subTest(case=case["id"]):
                text = report_for(case)
                self.assertTrue(text.startswith(IDENTITY_LINE))
                for page in text.split("\f"):
                    self.assertTrue(page.startswith(IDENTITY_LINE))

    def test_cli_report(self):
        done = run_cli(*G1_ARGS)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stderr, "")
        for page in done.stdout.split("\f"):
            self.assertTrue(page.startswith(IDENTITY_LINE))
        self.assertIn(case_by_id("G1")["expected"]["support"], done.stdout)

    def test_cli_rejects_unknown_flags(self):
        for extra in (["--no-identity"], ["--quiet"], ["--a-nd", "4000.00"]):
            with self.subTest(extra=extra):
                args = list(G1_ARGS)
                if extra[0] == "--a-nd":
                    args = args[2:]  # the abbreviation stands in for --a-ndi
                done = run_cli(*args, *extra)
                self.assertEqual(done.returncode, 2, done.stderr)
                self.assertEqual(done.stdout, "")
                self.assertEqual(len(done.stderr.strip().splitlines()), 1)

    def test_cli_rejects_bad_values(self):
        args = list(G1_ARGS)
        args[1] = "-5"
        done = run_cli(*args)
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertEqual(len(done.stderr.strip().splitlines()), 1)

    def test_report_has_no_forbidden_words(self):
        for case in load_cases():
            with self.subTest(case=case["id"]):
                text = report_for(case).lower()
                for word in FORBIDDEN_WORDS:
                    self.assertNotIn(word, text)

    def test_report_cites_subsections(self):
        cites = (
            "FC 4055(a)", "FC 4055(b)(3)", "FC 4055(b)(4)",
            "FC 4055(b)(5)", "FC 4055(b)(7)", "FC 4055(c)",
        )
        for case in load_cases():
            with self.subTest(case=case["id"]):
                text = report_for(case)
                for cite in cites:
                    self.assertIn(cite, text)

    def test_lia_shows_only_ranges(self):
        cases = {case["id"]: case for case in load_cases()}
        for case_id in ("G3", "G5", "G6"):
            with self.subTest(case=case_id):
                case = cases[case_id]
                lia = case["expected"]["lia"]
                self.assertTrue(lia["applies"])
                text = report_for(case)
                lines = text.split("\n")
                reduction = lia["max_reduction"]
                low = lia["range_low"]
                support = case["expected"]["support"]
                self.assertTrue(any("0.00 to " + reduction in l for l in lines))
                self.assertTrue(any("%s to %s" % (low, support) in l for l in lines))
                for line in lines:
                    if reduction in line:
                        self.assertIn("0.00 to ", line)
                    if low in line:
                        self.assertIn("%s to %s" % (low, support), line)
                self.assertIn(
                    "a rebuttable presumption that the paying parent is entitled to a "
                    "low-income adjustment applies (FC 4055(b)(7))",
                    text,
                )
                lowered = text.lower()
                self.assertNotIn("adjusted support", lowered)
                self.assertNotIn("after adjustment", lowered)
        plain_case = cases["G1"]
        self.assertFalse(plain_case["expected"]["lia"]["applies"])
        section = low_income_section(report_for(plain_case))
        for line in section:
            self.assertNotIn(" to ", line)

    def test_reading_r2_line_only_when_adjustment_applies(self):
        for case in load_cases():
            with self.subTest(case=case["id"]):
                text = report_for(case)
                lines = text.split("\n")
                if case["expected"]["lia"]["applies"]:
                    self.assertEqual(lines.count(READING_R2_LINE), 1)
                    self.assertIn(READING_R2_LINE, low_income_section(text))
                else:
                    self.assertNotIn(READING_R2_LINE, lines)
                    self.assertNotIn("This toolkit reads", text)
        self.assertEqual(
            READING_R2_LINE,
            "  This toolkit reads the monthly threshold as the hourly minimum wage "
            "x 40 x 52 / 12 (FC 4055(b)(7)).",
        )

    def test_no_internal_labels_in_printed_output(self):
        for case in load_cases():
            with self.subTest(case=case["id"]):
                for line in report_for(case).split("\n"):
                    for label in ("R1", "R2", "reading"):
                        self.assertNotIn(label, line)

    def test_threshold_line_wording(self):
        text = report_for(case_by_id("G1"))
        self.assertIn(
            "  Threshold (FC 4055(b)(7)): 3640.00 = hourly minimum wage x 40 x 52 / 12",
            text.split("\n"),
        )

    def test_hn_line_prints_high_earner_ndi(self):
        case = case_by_id("G8")
        self.assertEqual(case["expected"]["high_earner"], "B")
        lines = report_for(case).split("\n")
        hn_line = "  HN, the high earner's net disposable income: " + case["inputs"]["b_ndi"]
        self.assertIn(hn_line, lines)
        self.assertEqual(
            lines[lines.index(hn_line) + 1],
            "  Formula result, CS = K[HN - (H%)(TN)] (FC 4055(a)): "
            + case["expected"]["cs_formula"],
        )

    def test_symbol_lines_put_plain_words_first(self):
        lines = report_for(case_by_id("G8")).split("\n")
        self.assertIn(
            "  Total net disposable income, TN (FC 4055(b)(1)(E)): 11683.67", lines
        )
        self.assertIn(
            "  High earner's share of time, H% (FC 4055(b)(1)(D)): 40%", lines
        )

    def test_amount_lines_cite_formula_and_multiplier(self):
        saw_amount = saw_top = False
        for case in load_cases():
            with self.subTest(case=case["id"]):
                lines = report_for(case).split("\n")
                if case["expected"]["lia"]["applies"]:
                    saw_top = True
                    top = [l for l in lines if l.strip().startswith("Top of the support range")]
                    self.assertEqual(len(top), 1)
                    self.assertIn(
                        "before any low-income reduction (FC 4055(a), (b)(4)):", top[0]
                    )
                else:
                    saw_amount = True
                    amount = [l for l in lines if l.strip().startswith("Support amount")]
                    self.assertEqual(len(amount), 1)
                    self.assertIn("Support amount (FC 4055(a), (b)(4)):", amount[0])
                self.assertFalse(
                    any(
                        ("Support amount" in l or "Top of the support range" in l)
                        and "(b)(5)" in l
                        for l in lines
                    )
                )
                self.assertTrue(
                    any(l.startswith("  Paying parent (FC 4055(b)(5)): ") for l in lines)
                )
        self.assertTrue(saw_amount and saw_top)

    def test_rounding_note(self):
        self.assertIn(
            "Amounts are monthly dollars, rounded to the nearest cent (halves round up).",
            report_for(case_by_id("G1")).split("\n"),
        )

    def test_report_echoes_inputs(self):
        for case in load_cases():
            with self.subTest(case=case["id"]):
                inputs = case["inputs"]
                text = report_for(case)
                lines = text.split("\n")
                start = lines.index("Inputs as given")
                self.assertLess(start, lines.index("Formula"))
                self.assertLess(start, 8)  # at the top of the body
                section = lines[start:lines.index("Formula")]
                self.assertIn(
                    "  Parent A net disposable income: " + inputs["a_ndi"], section
                )
                self.assertIn(
                    "  Parent B net disposable income: " + inputs["b_ndi"], section
                )
                self.assertIn(
                    "  Parent A's share of time: %s%%" % inputs["a_time_percent"], section
                )
                self.assertIn(
                    "  Number of children: %d" % inputs["children"], section
                )
                self.assertIn(
                    "  Hourly state minimum wage used (Lab. Code 1182.12): "
                    + inputs["minimum_wage_hourly"],
                    section,
                )

    def test_adjustment_shows_range_and_no_single_figure(self):
        for case in load_cases():
            with self.subTest(case=case["id"]):
                text = report_for(case)
                lines = text.split("\n")
                lia = case["expected"]["lia"]
                if lia["applies"]:
                    self.assertIn(NO_SINGLE_FIGURE_LINE, lines)
                    self.assertTrue(
                        any(
                            ("%s to %s" % (lia["range_low"], lia["range_high"])) in l
                            for l in lines
                        )
                    )
                    # No line presents the single top figure as the support amount.
                    self.assertFalse(
                        any(l.strip().startswith("Support amount") for l in lines)
                    )
                else:
                    self.assertNotIn(NO_SINGLE_FIGURE_LINE, lines)
                    self.assertTrue(
                        any(l.strip().startswith("Support amount") for l in lines)
                    )

    def test_every_page_of_a_long_report_carries_identity_line(self):
        case = case_by_id("G3")
        with mock.patch.object(report, "BODY_LINES_PER_PAGE", 5):
            text = report_for(case)
        pages = text.split("\f")
        self.assertGreaterEqual(len(pages), 4)
        for page in pages:
            self.assertEqual(page.split("\n")[0], IDENTITY_LINE)

    def test_cli_exposes_no_way_to_suppress_identity_line(self):
        parser = cli_main._build_parser()
        flags = sorted(
            option for action in parser._actions for option in action.option_strings
        )
        self.assertEqual(
            flags,
            ["--a-ndi", "--a-time-percent", "--b-ndi", "--children",
             "--minimum-wage-hourly"],
        )
        # No environment variable is consulted by the report or the command line.
        for module in (report, cli_main):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("environ", source)
            self.assertNotIn("getenv", source)
        env = dict(os.environ, NO_IDENTITY="1", FAMILY_LAW_TOOLKIT_QUIET="1")
        done = subprocess.run(
            [sys.executable, "-m", "family_law_toolkit.support", *G1_ARGS],
            cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=60,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(done.stdout.startswith(IDENTITY_LINE))

    def test_report_notes_and_zero_case(self):
        text = report_for(load_cases()[0])
        self.assertIn(
            "You enter net disposable income yourself. "
            "This version does not work it out from deductions (FC 4059).",
            text,
        )
        self.assertIn(NOTE_TIME_SHARE, text)
        self.assertIn(
            "You enter the share of time yourself. "
            "The default-proceeding rule (FC 4055(b)(6)) is not applied.",
            text,
        )
        zero = render_report(compute("0", "0", "0", 1, "21.00"))
        self.assertIn("no paying parent", zero)
        self.assertIn(money(compute("0", "0", "0", 1, "21.00").support), zero)


    def test_wage_line_names_state_minimum_wage(self):
        for case in load_cases():
            with self.subTest(case=case["id"]):
                lines = report_for(case).split("\n")
                self.assertIn(
                    "  Hourly state minimum wage used (Lab. Code 1182.12): "
                    + case["inputs"]["minimum_wage_hourly"],
                    lines,
                )
                self.assertFalse(
                    any(l.startswith("  Hourly minimum wage used") for l in lines)
                )

    def test_presumption_sentence_when_adjustment_applies(self):
        sentence = (
            "  The paying parent's net disposable income is less than the threshold: "
            "a rebuttable presumption that the paying parent is entitled to a "
            "low-income adjustment applies (FC 4055(b)(7))."
        )
        for case in load_cases():
            with self.subTest(case=case["id"]):
                lines = report_for(case).split("\n")
                if case["expected"]["lia"]["applies"]:
                    self.assertEqual(lines.count(sentence), 1)
                else:
                    self.assertNotIn(sentence, lines)

    def test_per_child_scope_note_only_with_two_or_more_children(self):
        note = "The per-child allocation (FC 4055(b)(8)) is not shown."
        for case in load_cases():
            with self.subTest(case=case["id"]):
                lines = report_for(case).split("\n")
                if case["inputs"]["children"] >= 2:
                    self.assertIn(note, lines)
                else:
                    self.assertNotIn(note, lines)
                    self.assertNotIn("per-child", "\n".join(lines))

    def test_per_child_scope_note_appears_once_after_time_share_note(self):
        note = "The per-child allocation (FC 4055(b)(8)) is not shown."
        for case_id in ("G2", "G3", "G8"):
            with self.subTest(case=case_id):
                text = report_for(case_by_id(case_id))
                lines = text.split("\n")
                self.assertEqual(text.count("per-child allocation"), 1)
                self.assertEqual(lines.count(note), 1)
                self.assertEqual(lines.index(note), lines.index(NOTE_TIME_SHARE) + 1)


if __name__ == "__main__":
    unittest.main()
