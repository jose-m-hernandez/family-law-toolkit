# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Tests for the plain-text report, the identity line and the command line."""

import inspect
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from family_law_toolkit import TOOLKIT_NAME, __version__
from family_law_toolkit.support import __main__ as cli_main
from family_law_toolkit.support import guideline, report
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
GOLDEN_STEP2_PATH = ROOT / "tests" / "golden" / "guideline_step2.json"
GOLDEN_REPORTS_PATH = ROOT / "tests" / "golden" / "guideline_step1_reports.json"
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


FLAG = "--same-time-sharing-arrangement"
HEADING_OLD = "Guideline child support, step 1 (California Family Code section 4055)"
HEADING_NEW = "Guideline child support (California Family Code section 4055)"
CLOSING_LINE_TEXT = (
    "This report is arithmetic on the figures you entered. It is not legal advice."
)
E1_LINE = "The per-child allocation (FC 4055(b)(8)) is not shown."
E2_LINE = (
    "The per-child allocation (FC 4055(b)(8)) is shown only if you add "
    "--same-time-sharing-arrangement yes. It does not apply when the children "
    "have different time-sharing arrangements."
)
E3_LINE = (
    "The per-child allocation (FC 4055(b)(8)) does not apply, because the "
    "children have different time-sharing arrangements."
)
E4_LINE = (
    "Guideline support is 0.00, so there is no amount to allocate per child "
    "(FC 4055(b)(8))."
)
C1_LINE = "Allocation per child (FC 4055(b)(8))"
C2_LINE = (
    "  The statute uses this allocation unless the court orders otherwise "
    "(FC 4055(b)(8))."
)
C5_SUPPORT_LINE = (
    "  Child 1 is the amount of support for 1 child. Child 2 is the amount for 2 "
    "children less the amount for 1 child, and so on. Together they add up to "
    "the support amount above."
)
C5_END_LINE = (
    "  Child 1 is the amount of support for 1 child. Child 2 is the amount for 2 "
    "children less the amount for 1 child, and so on. Together they add up to "
    "that end of the range."
)
C6_LINE = (
    "  This toolkit rounds the amount for each number of children to the cent "
    "before taking the differences; FC 4055 does not say how to round."
)
C7_LINE = (
    "  Where an amount above shows 0.00, the exact amount is above zero but "
    "under one cent. It shows 0.00 because this toolkit rounds the running "
    "totals to the cent before taking the differences. It is not an allocation "
    "of zero support."
)
D1_LINE = "  At the top of the support range (no low-income reduction):"
D2_LINE = "  At the bottom of the support range (the largest permitted reduction):"
D3_LINE = (
    "  The court sets the amount within the range, and FC 4055(b)(8) then "
    "allocates the amount it orders. No allocation is shown for amounts between "
    "the two ends shown."
)
D4_LINE = (
    "  This toolkit applies the largest reduction to the amount for each number "
    "of children; FC 4055(b)(7) does not say that the (b)(8) amounts are adjusted."
)
CHILD_RE = re.compile(
    r"^  Child (\d+)(, youngest|, oldest)? \(FC 4055\(b\)\(8\)\): (-?\d+\.\d\d)$"
)
CUM_RE = re.compile(
    r"^  Amount of support for (\d+) (?:child|children) \(FC 4055\(b\)\(4\)\): (-?\d+\.\d\d)$"
)
RANGE_RE = re.compile(r"^  Support range \(FC 4055\(c\)\): (\d+\.\d\d) to (\d+\.\d\d)$")
SUPPORT_RE = re.compile(r"^  Support amount \(FC 4055\(a\), \(b\)\(4\)\): (\d+\.\d\d)$")

# Money inputs of S1 and S4 (invented), reused for the 2-10 children sweeps.
S1_MONEY = ("6919.09", "2255.71", "35")
S4_MONEY = ("2258.50", "612.53", "45")


def render_for(a_ndi, b_ndi, a_time, children, flag=None, wage="21.00"):
    kwargs = {} if flag is None else {"same_time_sharing_arrangement": flag}
    return render_report(compute(a_ndi, b_ndi, a_time, children, wage, **kwargs))


def lines_of(text):
    """Report lines with the page headers (identity line and blank line) dropped."""
    lines = []
    for page in text.split("\f"):
        lines += page.split("\n")[2:]
    return lines


def step2_cases():
    with GOLDEN_STEP2_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)["cases"]


def step2_report(case):
    inputs = case["inputs"]
    return render_for(
        inputs["a_ndi"], inputs["b_ndi"], inputs["a_time_percent"],
        inputs["children"], inputs["same_time_sharing_arrangement"],
        inputs["minimum_wage_hourly"],
    )


def cents(text):
    whole, part = text.split(".")
    return int(whole) * 100 + int(part)


def block_lines(text):
    """The allocation block: from its heading to the next blank line (or the end)."""
    lines = lines_of(text)
    start = lines.index(C1_LINE)
    end = start
    while end < len(lines) and lines[end] != "":
        end += 1
    return lines[start:end]


def end_groups(text):
    """Per range end: {'cumulative': [...], 'per_child': [...]} in cents.

    A report without a range has one group ('top'); under R7 it has 'top' and
    'bottom', split at the D1 and D2 lines.
    """
    block = block_lines(text)
    if D1_LINE in block:
        marks = [("top", block.index(D1_LINE)), ("bottom", block.index(D2_LINE))]
        spans = {
            "top": block[marks[0][1]:marks[1][1]],
            "bottom": block[marks[1][1]:],
        }
    else:
        spans = {"top": block}
    groups = {}
    for name, span in spans.items():
        cumulative = [cents(m.group(2)) for m in map(CUM_RE.match, span) if m]
        per_child = [cents(m.group(3)) for m in map(CHILD_RE.match, span) if m]
        groups[name] = {"cumulative": cumulative, "per_child": per_child}
    return groups


def printed_figures(text):
    """The cents the report prints: {'top': cents, 'bottom': cents or absent}."""
    for line in lines_of(text):
        match = RANGE_RE.match(line)
        if match:
            return {"bottom": cents(match.group(1)), "top": cents(match.group(2))}
    for line in lines_of(text):
        match = SUPPORT_RE.match(line)
        if match:
            return {"top": cents(match.group(1))}
    raise AssertionError("no printed support figure")


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

    def test_cli_value_errors_name_the_flag_typed(self):
        base = {
            "--a-ndi": "6919.09",
            "--b-ndi": "2255.71",
            "--a-time-percent": "35",
            "--children": "2",
            "--minimum-wage-hourly": "21.00",
        }
        prefix = "python3 -m family_law_toolkit.support: error: "
        cases = (
            ("--a-ndi", "1,000", "is not a decimal number"),
            ("--a-ndi", "NaN", "must be a finite number"),
            ("--a-ndi", "4000.001", "has more than 2 decimals"),
            ("--a-ndi", "1E+30", "is too large"),
            ("--b-ndi", "-0.01", "must not be negative"),
            ("--a-time-percent", "100.01", "must be between 0 and 100"),
            ("--children", "11", "must be between 1 and 10"),
            ("--minimum-wage-hourly", "0", "must be greater than zero"),
        )
        for flag, value, rest in cases:
            with self.subTest(flag=flag, value=value):
                values = dict(base)
                values[flag] = value
                argv = []
                for name, text in values.items():
                    argv.extend([name, text])
                done = run_cli(*argv)
                self.assertEqual(done.returncode, 2, done.stderr)
                self.assertEqual(done.stdout, "")
                lines = done.stderr.splitlines()
                self.assertEqual(len(lines), 1, done.stderr)
                self.assertEqual(lines[0], prefix + flag + " " + rest)
                self.assertNotIn("_", lines[0][len(prefix):])
                self.assertNotIn(value, lines[0][len(prefix):])

    def test_cli_help_prints_help_and_exits_0(self):
        outputs = []
        for flag in ("--help", "-h"):
            with self.subTest(flag=flag):
                done = run_cli(flag)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertEqual(done.stderr, "")
                self.assertTrue(done.stdout)
                lines = done.stdout.split("\n")
                heading = "Guideline child support (California Family Code section 4055)"
                self.assertEqual(
                    lines[lines.index(heading) + 1],
                    "Educational; not legal advice; not certified for court filing;"
                    " consult counsel.",
                )
                outputs.append(done.stdout)
        self.assertEqual(outputs[0], outputs[1])

    def test_cli_help_wins_over_other_arguments(self):
        plain = run_cli("--help").stdout
        valid = list(cli_args(case_by_id("G1")))
        placed = {
            "before": ["--help"] + valid,
            "among": valid[:4] + ["--help"] + valid[4:],
            "after": valid + ["--help"],
            "short with invalid value": ["-h", "--children", "two"],
        }
        for label, argv in placed.items():
            with self.subTest(placement=label):
                done = run_cli(*argv)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertEqual(done.stdout, plain)
                self.assertNotIn(IDENTITY_LINE, done.stdout)

    def test_cli_help_names_every_parser_option(self):
        text = run_cli("--help").stdout
        for action in cli_main._build_parser()._actions:
            for option in action.option_strings:
                with self.subTest(option=option):
                    self.assertIn(option, text)

    def test_cli_help_carries_the_reviewed_strings(self):
        text = " ".join(run_cli("--help").stdout.split())
        expected = (
            "Guideline child support (California Family Code section 4055)",
            "Educational; not legal advice; not certified for court filing;"
            " consult counsel.",
            "Parent A net disposable income",
            "Parent B net disposable income",
            "Parent A's share of time",
            "Number of children",
            "Hourly state minimum wage used (Lab. Code 1182.12)",
            "All children share one time-sharing arrangement",
            report.NOTE_NDI,
            NOTE_TIME_SHARE,
            report.NOTE_PER_CHILD_NO_FLAG,
            "It has an effect only with two or more children.",
            "Net disposable income amounts are monthly dollars; the minimum wage"
            " is per hour.",
            "Parent A and Parent B are labels for the two parents. Use the same"
            " labels for every input.",
            "Write AMOUNT and PERCENT as plain numbers with at most two decimals,"
            " such as 6919.09: no commas, no dollar sign. PERCENT is from 0 to"
            " 100. COUNT is a whole number from 1 to 10.",
            "Example, with invented numbers:",
            "python3 -m family_law_toolkit.support --a-ndi 6919.09 --b-ndi 2255.71"
            " --a-time-percent 35 --children 2 --minimum-wage-hourly 21.00",
        )
        for piece in expected:
            with self.subTest(piece=piece[:40]):
                self.assertIn(piece, text)

    def test_cli_help_text_rules(self):
        text = run_cli("--help").stdout
        for word in FORBIDDEN_WORDS:
            with self.subTest(word=word):
                self.assertNotIn(word, text.lower())
        long_lines = [line for line in text.split("\n") if len(line) > 79]
        self.assertEqual(len(long_lines), 1, long_lines)
        self.assertTrue(
            long_lines[0].startswith("    python3 -m family_law_toolkit.support --a-ndi")
        )

    def test_cli_usage_errors_point_to_help(self):
        tail = ". Run with --help to see what each flag means."
        attempts = {
            "no arguments": (),
            "unknown flag": G1_ARGS + ("--quiet",),
            "bad choice": G1_ARGS + (FLAG, "maybe"),
        }
        for label, argv in attempts.items():
            with self.subTest(case=label):
                done = run_cli(*argv)
                self.assertEqual(done.returncode, 2, done.stderr)
                self.assertEqual(done.stdout, "")
                lines = done.stderr.splitlines()
                self.assertEqual(len(lines), 1, done.stderr)
                self.assertTrue(lines[0].endswith(tail), lines[0])

    def test_cli_children_1_output_does_not_depend_on_the_arrangement_flag(self):
        money_args = list(G1_ARGS)
        money_args[money_args.index("--children") + 1] = "1"
        without = run_cli(*money_args)
        with_flag = run_cli(*money_args, FLAG, "yes")
        self.assertEqual(without.returncode, 0, without.stderr)
        self.assertEqual(with_flag.returncode, 0, with_flag.stderr)
        self.assertEqual(without.stdout, with_flag.stdout)

    def test_readme_example_command_runs(self):
        lines = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
        prefix = "python3 -m family_law_toolkit.support "
        matches = [line for line in lines if line.lstrip().startswith(prefix)]
        self.assertEqual(len(matches), 1)
        tokens = matches[0].split()
        self.assertEqual(tokens[:3], ["python3", "-m", "family_law_toolkit.support"])
        result = run_cli(*tokens[3:])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn(
            "Guideline child support (California Family Code section 4055)",
            result.stdout,
        )

    def test_readme_python_version_matches_ci_minimum(self):
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        matches = [line for line in ci.splitlines() if "python-version: [" in line]
        self.assertEqual(len(matches), 1)
        version = matches[0].split('"')[1]
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Needs Python " + version + " or later", readme)

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
             "--minimum-wage-hourly", "--same-time-sharing-arrangement"],
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

    def test_old_per_child_note_is_printed_for_no_child_count(self):
        # The old note (E1) is gone for every child count and every flag state.
        old = "The per-child allocation (FC 4055(b)(8)) is not shown."
        for children in range(1, 11):
            for flag in (None, "yes", "no"):
                with self.subTest(children=children, flag=flag):
                    self.assertNotIn(old, render_for("4000.00", "2000.00", "20", children, flag))
        for case in load_cases():
            with self.subTest(case=case["id"]):
                self.assertNotIn(old, report_for(case))

    def test_per_child_note_without_flag_appears_once_after_time_share_note(self):
        # R10: the how-to line (E2) replaces the old note; only with 2+ children.
        for case_id in ("G2", "G3", "G8"):
            with self.subTest(case=case_id):
                text = report_for(case_by_id(case_id))
                lines = text.split("\n")
                self.assertEqual(text.count("per-child allocation"), 1)
                self.assertEqual(lines.count(E2_LINE), 1)
                self.assertEqual(lines.index(E2_LINE), lines.index(NOTE_TIME_SHARE) + 1)
        for case_id in ("G1", "G4", "G5", "G6"):
            with self.subTest(case=case_id):
                self.assertNotIn("per-child", report_for(case_by_id(case_id)))


class AllocationReportTests(unittest.TestCase):
    """Step 2: the FC 4055(b)(8) allocation per child (plan section 7)."""

    def test_1_flag_yes_prints_one_labelled_line_per_child(self):  # test 1
        for children in (2, 3, 4):
            with self.subTest(children=children):
                text = render_for(*S1_MONEY, children, "yes")
                lines = lines_of(text)
                self.assertIn(C1_LINE, lines)
                self.assertIn(C2_LINE, lines)
                child_lines = [l for l in lines if CHILD_RE.match(l)]
                self.assertEqual(len(child_lines), children)
                for position, line in enumerate(child_lines, start=1):
                    tag = ""
                    if position == 1:
                        tag = ", youngest"
                    if position == children:
                        tag = ", oldest"
                    self.assertTrue(
                        line.startswith("  Child %d%s (FC 4055(b)(8)): " % (position, tag)),
                        line,
                    )
                cumulative = [l for l in lines if CUM_RE.match(l)]
                self.assertEqual(len(cumulative), children)
                for count, line in enumerate(cumulative, start=1):
                    noun = "child" if count == 1 else "children"
                    self.assertTrue(
                        line.startswith(
                            "  Amount of support for %d %s (FC 4055(b)(4)): " % (count, noun)
                        ),
                        line,
                    )
                # R11(c): the cumulative amounts come before the differences.
                self.assertLess(lines.index(cumulative[-1]), lines.index(child_lines[0]))
                self.assertIn(C5_SUPPORT_LINE, lines)
                self.assertIn(C6_LINE, lines)
                self.assertNotIn(D1_LINE, lines)

    def test_1_two_children_are_youngest_and_oldest(self):
        lines = lines_of(render_for(*S1_MONEY, 2, "yes"))
        tags = [m.group(2) for m in map(CHILD_RE.match, lines) if m]
        self.assertEqual(tags, [", youngest", ", oldest"])

    def test_2_per_child_amounts_add_to_the_printed_figure(self):  # test 2
        reports = [(case["id"], step2_report(case)) for case in step2_cases()]
        for money_inputs in (S1_MONEY, S4_MONEY):
            for children in range(2, 11):
                reports.append(
                    ("%s/%d" % (money_inputs[0], children),
                     render_for(*money_inputs, children, "yes"))
                )
        for name, text in reports:
            with self.subTest(case=name):
                groups = end_groups(text)
                printed = printed_figures(text)
                self.assertEqual(set(groups), set(printed))
                for end, group in groups.items():
                    self.assertEqual(sum(group["per_child"]), printed[end])
                    self.assertEqual(group["cumulative"][-1], printed[end])

    def test_2_s5_per_child_amounts_are_differences_of_shown_running_totals(self):
        # Guards R8: the displayed per-child amounts add up to the shown figure,
        # because they are differences of the displayed running totals. The other
        # rounding order (each exact difference rounded alone) is checked by the
        # next test.
        text = step2_report(next(c for c in step2_cases() if c["id"] == "S5"))
        group = end_groups(text)["top"]
        self.assertEqual(sum(group["per_child"]), printed_figures(text)["top"])
        self.assertEqual(
            group["per_child"],
            [group["cumulative"][0]]
            + [b - a for a, b in zip(group["cumulative"], group["cumulative"][1:])],
        )

    def test_2_s5_rounding_each_exact_difference_alone_misses_the_shown_total(self):
        case = next(c for c in step2_cases() if c["id"] == "S5")
        inputs = case["inputs"]
        result = compute(
            inputs["a_ndi"], inputs["b_ndi"], inputs["a_time_percent"],
            inputs["children"], inputs["minimum_wage_hourly"],
            same_time_sharing_arrangement=inputs["same_time_sharing_arrangement"],
        )
        exact = guideline.allocation(result).top.exact_cumulative
        differences = [exact[0]] + [b - a for a, b in zip(exact, exact[1:])]
        # Half-up to whole cents, written out here so the comparison does not
        # depend on the calculator's own rounding helpers.
        # floor(d * 100 + 1/2) written as floor((d * 200 + 1) / 2): Fraction floor division.
        alone = [(d * 200 + 1) // 2 for d in differences]
        # These values come from docs/derivations/guideline-step-2.md (the S5 check).
        self.assertEqual(alone, [112921, 67753, 45168, 33876])
        text = step2_report(case)
        shown = printed_figures(text)["top"]
        self.assertEqual(sum(alone), 259718)
        self.assertEqual(shown, 259719)
        self.assertNotEqual(sum(alone), shown)
        per_child = end_groups(text)["top"]["per_child"]
        self.assertNotEqual(alone, per_child)
        self.assertEqual(len(alone), len(per_child))
        self.assertEqual(alone[:-1], per_child[:-1])
        self.assertNotEqual(alone[-1], per_child[-1])

    def test_3_one_child_prints_no_allocation(self):  # test 3
        for flag in (None, "yes", "no"):
            with self.subTest(flag=flag):
                text = render_for(*S1_MONEY, 1, flag)
                self.assertNotIn(C1_LINE, text)
                self.assertNotIn("Child 1", text)
                self.assertNotIn("per-child", text)

    def test_5_b_pays_allocates_the_amount_b_pays(self):  # test 5
        case = next(c for c in step2_cases() if c["id"] == "S2")
        text = step2_report(case)
        lines = lines_of(text)
        self.assertIn("  Paying parent (FC 4055(b)(5)): Parent B", lines)
        self.assertEqual(
            [m.group(3) for m in map(CHILD_RE.match, lines) if m],
            case["expected"]["allocation"]["top"]["per_child"],
        )

    def test_6_golden_step2_cases_match_to_the_cent(self):  # test 6
        for case in step2_cases():
            with self.subTest(case=case["id"]):
                groups = end_groups(step2_report(case))
                expected = case["expected"]["allocation"]
                self.assertEqual(set(groups), set(expected))
                for end, group in groups.items():
                    self.assertEqual(
                        group["cumulative"], [cents(v) for v in expected[end]["cumulative"]]
                    )
                    self.assertEqual(
                        group["per_child"], [cents(v) for v in expected[end]["per_child"]]
                    )

    def test_7_identity_line_on_every_page_with_the_allocation(self):  # test 7
        for money_inputs in (S1_MONEY, S4_MONEY):
            for children in (2, 5, 10):
                with self.subTest(money=money_inputs[0], children=children):
                    text = render_for(*money_inputs, children, "yes")
                    for page in text.split("\f"):
                        lines = page.split("\n")
                        self.assertEqual(lines[0], IDENTITY_LINE)
                        self.assertEqual(lines[1], "")
                        self.assertLessEqual(len(lines), report.PAGE_LINES)
        self.assertGreaterEqual(len(render_for(*S4_MONEY, 10, "yes").split("\f")), 2)

    def test_8_range_shows_both_ends_and_nothing_inside(self):  # test 8
        case = next(c for c in step2_cases() if c["id"] == "S4")
        lines = lines_of(step2_report(case))
        self.assertEqual(lines.count(C1_LINE), 1)
        self.assertEqual(lines.count(C2_LINE), 1)
        self.assertEqual(lines.count(D1_LINE), 1)
        self.assertEqual(lines.count(D2_LINE), 1)
        self.assertEqual(lines.count(C5_END_LINE), 2)
        self.assertEqual(lines.count(C5_SUPPORT_LINE), 0)
        self.assertEqual(lines.count(C6_LINE), 1)
        self.assertEqual(lines.count(D3_LINE), 1)
        self.assertEqual(lines.count(D4_LINE), 1)
        self.assertLess(lines.index(D1_LINE), lines.index(D2_LINE))
        self.assertLess(lines.index(D2_LINE), lines.index(C6_LINE))
        self.assertLess(lines.index(C6_LINE), lines.index(D3_LINE))
        self.assertLess(lines.index(D3_LINE), lines.index(D4_LINE))
        # Exactly two sets of per-child lines (3 children each), none for a point inside.
        self.assertEqual(len([l for l in lines if CHILD_RE.match(l)]), 6)
        self.assertEqual(len([l for l in lines if CUM_RE.match(l)]), 6)
        self.assertIn("  Support range (FC 4055(c)): 347.22 to 559.61", lines)

    def test_10_r10_three_states(self):  # test 10
        for children in (2, 3, 10):
            with self.subTest(children=children):
                absent = lines_of(render_for(*S1_MONEY, children))
                no = lines_of(render_for(*S1_MONEY, children, "no"))
                yes = lines_of(render_for(*S1_MONEY, children, "yes"))
                self.assertEqual(absent.count(E2_LINE), 1)
                self.assertNotIn(E3_LINE, absent)
                self.assertNotIn(C1_LINE, absent)
                self.assertEqual(no.count(E3_LINE), 1)
                self.assertNotIn(E2_LINE, no)
                self.assertNotIn(C1_LINE, no)
                self.assertIn(C1_LINE, yes)
                self.assertNotIn(E2_LINE, yes)
                self.assertNotIn(E3_LINE, yes)
                self.assertNotIn(E1_LINE, yes)
                # A3: the echo is the last line of "Inputs as given", only with the flag.
                echo = "  All children share one time-sharing arrangement: "
                self.assertFalse(any(l.startswith(echo) for l in absent))
                self.assertEqual(
                    no[no.index("Formula") - 2], echo + "no"
                )
                self.assertEqual(
                    yes[yes.index("Formula") - 2], echo + "yes"
                )
                self.assertEqual(no[no.index("Formula") - 1], "")
        for children in (1,):
            reports = {render_for(*S1_MONEY, children, flag) for flag in (None, "yes", "no")}
            self.assertEqual(len(reports), 1)

    def test_10_cli_flag_accepted_and_rejected(self):
        done = run_cli(*G1_ARGS, FLAG, "yes")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout, run_cli(*G1_ARGS).stdout)
        case = next(c for c in step2_cases() if c["id"] == "S1")
        done = run_cli(*cli_args(case), FLAG, "yes")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout, step2_report(case) + "\n")
        done = run_cli(*cli_args(case), FLAG, "maybe")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stdout, "")
        self.assertEqual(len(done.stderr.strip().splitlines()), 1)
        self.assertIn(
            "python3 -m family_law_toolkit.support: error: argument "
            "--same-time-sharing-arrangement: invalid choice: 'maybe'",
            done.stderr,
        )
        done = run_cli(*cli_args(case), FLAG)
        self.assertEqual(done.returncode, 2)

    def test_11_negative_result_names_the_payer_once(self):  # test 11
        text = render_for("5000.00", "8000.00", "30", 3, "yes")
        lines = lines_of(text)
        self.assertEqual(lines.count("  Paying parent (FC 4055(b)(5)): Parent A"), 1)
        for line in block_lines(text):
            self.assertNotIn("Parent", line)
        for line in lines:
            match = CHILD_RE.match(line) or CUM_RE.match(line)
            if match:
                self.assertNotIn("-", match.group(match.lastindex))
        # The S2 report is the negative-total case in the golden file.
        s2 = step2_report(next(c for c in step2_cases() if c["id"] == "S2"))
        self.assertIn("  CS times multiplier (FC 4055(b)(4)): -263.80", lines_of(s2))
        for case in step2_cases():
            self.assertNotIn("the amount for each child", step2_report(case).lower())

    def test_12_step1_reports_change_only_by_the_pinned_lines(self):  # test 12
        with GOLDEN_REPORTS_PATH.open(encoding="utf-8") as handle:
            fixture = json.load(handle)
        self.assertEqual(sorted(fixture), ["G%d" % n for n in range(1, 9)])
        for case in load_cases():
            with self.subTest(case=case["id"]):
                old = fixture[case["id"]]
                lines = old.split("\n")
                self.assertEqual(lines.count(HEADING_OLD), 1)
                lines[lines.index(HEADING_OLD)] = HEADING_NEW
                if case["inputs"]["children"] >= 2:
                    self.assertEqual(lines.count(E1_LINE), 1)
                    lines[lines.index(E1_LINE)] = E2_LINE
                else:
                    self.assertNotIn(E1_LINE, lines)
                done = run_cli(*cli_args(case))
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertEqual(lines[-1], "")  # the fixture ends with a newline
                lines[-1:] = ["", CLOSING_LINE_TEXT, ""]  # the closing line
                self.assertEqual(done.stdout, "\n".join(lines))

    def test_13_i_ii_no_negative_and_every_exact_amount_positive(self):  # test 13 (i), (ii)
        for money_inputs in (S1_MONEY, S4_MONEY, ("10000.00", "10.00", "100")):
            for children in range(2, 11):
                with self.subTest(money=money_inputs[0], children=children):
                    result = compute(*money_inputs, children, "21.00",
                                     same_time_sharing_arrangement="yes")
                    self.assertGreater(result.support, 0)
                    text = render_report(result)
                    for group in end_groups(text).values():
                        self.assertTrue(all(c >= 0 for c in group["per_child"]))
                    allocation = guideline.allocation(result)
                    ends = [allocation.top] + ([allocation.bottom] if allocation.bottom else [])
                    for end in ends:
                        exact = end.exact_cumulative
                        steps = [exact[0]] + [b - a for a, b in zip(exact, exact[1:])]
                        self.assertTrue(all(step > 0 for step in steps))

    def test_13_iii_c7_prints_if_and_only_if_a_block_amount_shows_zero(self):
        # (a) tiny payer NDI 1.00 (payer B, H% 100, wage 21.00): the top end has
        # 0.25 and 0.15, the bottom end is the top end times 1.00/3640.00, which
        # displays 0.00 for both children, so only the bottom end has zeros.
        text = render_for("10000.00", "1.00", "100", 2, "yes")
        groups = end_groups(text)
        self.assertEqual(groups["top"]["per_child"], [25, 15])
        self.assertEqual(groups["bottom"]["per_child"], [0, 0])
        self.assertEqual(lines_of(text).count(C7_LINE), 1)
        block = block_lines(text)
        self.assertEqual(block[-1], C7_LINE)  # after D3 and D4
        self.assertEqual(block[-3:-1], [D3_LINE, D4_LINE])
        # (b) 10 children, payer NDI 10.00: the bottom end displays 0.01 then
        # runs of 0.00 and 0.01, so some but not all lines show 0.00.
        text = render_for("10000.00", "10.00", "100", 10, "yes")
        groups = end_groups(text)
        self.assertIn(0, groups["bottom"]["per_child"])
        self.assertTrue(any(c > 0 for c in groups["bottom"]["per_child"]))
        self.assertEqual(lines_of(text).count(C7_LINE), 1)
        # (c) no zero anywhere: S1 and S4 have no C7.
        for money_inputs, children in ((S1_MONEY, 2), (S4_MONEY, 3)):
            text = render_for(*money_inputs, children, "yes")
            self.assertNotIn(C7_LINE, lines_of(text))
            self.assertTrue(all(c > 0 for g in end_groups(text).values() for c in g["per_child"]))
        # (d) the iff, over a sweep.
        for money_inputs in (S1_MONEY, S4_MONEY, ("10000.00", "10.00", "100"),
                             ("10000.00", "1.00", "100"), ("10000.00", "100.00", "100")):
            for children in range(2, 11):
                with self.subTest(money=money_inputs[1], children=children):
                    text = render_for(*money_inputs, children, "yes")
                    has_zero = any(
                        0 in g["per_child"] for g in end_groups(text).values()
                    )
                    self.assertEqual(lines_of(text).count(C7_LINE), 1 if has_zero else 0)

    def test_13_iv_no_paying_parent_prints_e4_only(self):
        # Both incomes 0 (as in test_zero_incomes), and equal incomes at 50%.
        for inputs in (("0", "0", "0"), ("5000.00", "5000.00", "50")):
            for children in (2, 3, 10):
                with self.subTest(inputs=inputs, children=children):
                    text = render_for(*inputs, children, "yes")
                    lines = lines_of(text)
                    self.assertIn("  Paying parent (FC 4055(b)(5)): none", lines)
                    self.assertEqual(lines.count(E4_LINE), 1)
                    self.assertNotIn(C1_LINE, lines)
                    self.assertNotIn(C7_LINE, lines)
                    self.assertNotIn(E1_LINE, lines)
                    self.assertNotIn(E2_LINE, lines)
                    self.assertNotIn(E3_LINE, lines)
                    self.assertFalse(any(CHILD_RE.match(l) for l in lines))
                    self.assertEqual(lines.index(E4_LINE), lines.index(NOTE_TIME_SHARE) + 1)
            # One child: the flag has no effect, so no E4.
            self.assertNotIn(E4_LINE, render_for(*inputs, 1, "yes"))
        # Flag absent or no: E4 does not replace E2 or E3.
        self.assertNotIn(E4_LINE, render_for("0", "0", "0", 2))
        self.assertNotIn(E4_LINE, render_for("0", "0", "0", 2, "no"))

    def test_13_v_tiny_positive_total_names_a_payer_and_shows_the_block(self):
        # Exact total above 0 that displays 0.00. (a) payer NDI 0.01 (A, H% 0): the
        # total is about 0.0026 and the low-income test applies. (b) 5000.00 and
        # 4999.99 at 50%: HN - H% x TN is 0.005, the total about 0.003, and the
        # payer's NDI is over the threshold, so one block and no range.
        for inputs, ranged in ((("0.01", "0.00", "0"), True),
                               (("5000.00", "4999.99", "50"), False)):
            with self.subTest(inputs=inputs):
                text = render_for(*inputs, 2, "yes")
                lines = lines_of(text)
                self.assertIn("  Paying parent (FC 4055(b)(5)): Parent A", lines)
                self.assertIn(C1_LINE, lines)
                self.assertEqual(lines.count(C7_LINE), 1)
                self.assertNotIn(E4_LINE, lines)
                self.assertEqual(D1_LINE in lines, ranged)
                for group in end_groups(text).values():
                    self.assertEqual(group["per_child"], [0, 0])

    def test_14_parser_has_exactly_six_options_one_optional(self):  # test 14
        parser = cli_main._build_parser()
        self.assertFalse(parser.add_help)
        options = {}
        for action in parser._actions:
            for option in action.option_strings:
                options[option] = action
        self.assertEqual(
            sorted(options),
            ["--a-ndi", "--a-time-percent", "--b-ndi", "--children",
             "--minimum-wage-hourly", FLAG],
        )
        for name, action in options.items():
            if name == FLAG:
                self.assertFalse(action.required)
                self.assertEqual(list(action.choices), ["yes", "no"])
            else:
                self.assertTrue(action.required, name)

    def test_report_text_rules(self):
        # Standing rules for every string: no forbidden words, new heading, no old one.
        texts = [step2_report(case) for case in step2_cases()]
        texts += [render_for(*S1_MONEY, 3), render_for(*S1_MONEY, 3, "no"),
                  render_for("0", "0", "0", 2, "yes")]
        for text in texts:
            lowered = text.lower()
            for word in FORBIDDEN_WORDS:
                self.assertNotIn(word, lowered)
            self.assertNotIn("the amount for each child", lowered)
            lines = lines_of(text)
            self.assertEqual(lines[0], HEADING_NEW)
            self.assertNotIn(HEADING_OLD, lines)


if __name__ == "__main__":
    unittest.main()
