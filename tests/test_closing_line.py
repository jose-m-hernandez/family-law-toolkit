# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""The support report ends with one closing line, after one blank line, in
every variant, and the first line is unchanged. The command has no option
that turns the closing line off."""

import unittest

from family_law_toolkit import TOOLKIT_NAME, __version__
from family_law_toolkit.support import guideline
from family_law_toolkit.support.report import render_report
from tests.test_report import run_cli

CLOSING = "This report is arithmetic on the figures you entered. It is not legal advice."
FIRST = (
    TOOLKIT_NAME
    + " v"
    + __version__
    + " — not certified for court filing; not affiliated with DissoMaster or XSpouse"
)
FLAG = "--same-time-sharing-arrangement"
README_ARGS = (
    "--a-ndi", "9500.00", "--b-ndi", "3500.00", "--a-time-percent", "15",
    "--children", "3", "--minimum-wage-hourly", "21.00",
)
LIA_ARGS = (
    "--a-ndi", "3000.00", "--b-ndi", "500.00", "--a-time-percent", "25",
    "--children", "3", "--minimum-wage-hourly", "21.00",
)
ZERO_ARGS = (
    "--a-ndi", "0", "--b-ndi", "0", "--a-time-percent", "50",
    "--children", "2", "--minimum-wage-hourly", "21.00",
)
FIVE_CHILDREN_ARGS = (
    "--a-ndi", "1000", "--b-ndi", "100", "--a-time-percent", "35",
    "--children", "5", "--minimum-wage-hourly", "21.00",
)
VARIANTS = {
    "one child": (README_ARGS[:7] + ("1",) + README_ARGS[8:]),
    "three children, no flag": README_ARGS,
    "three children, flag yes (allocation)": README_ARGS + (FLAG, "yes"),
    "three children, flag no": README_ARGS + (FLAG, "no"),
    "low-income adjustment, flag yes (allocation at both ends)": LIA_ARGS + (FLAG, "yes"),
    "low-income adjustment, no flag": LIA_ARGS,
    "a share per child, shares differ": (
        README_ARGS[:6] + ("--a-time-percent", "40", "--a-time-percent", "15") + README_ARGS[6:]
    ),
    "a share per child, shares equal, flag yes": (
        README_ARGS[:6] + ("--a-time-percent", "15", "--a-time-percent", "15") + README_ARGS[6:] + (FLAG, "yes")
    ),
    "no paying parent, flag yes": ZERO_ARGS + (FLAG, "yes"),
    "five children, flag yes (two pages)": FIVE_CHILDREN_ARGS + (FLAG, "yes"),
}


def check_ends_with_closing_line(test, text):
    lines = text.split("\n")
    test.assertEqual(lines[-1], "")  # the command's final newline
    test.assertEqual(lines[-2], CLOSING)
    test.assertEqual(lines[-3], "")
    test.assertNotEqual(lines[-4], "")
    test.assertEqual(text.count(CLOSING), 1)


class ClosingLineTests(unittest.TestCase):
    def test_every_variant_ends_with_a_blank_line_then_the_closing_line(self):
        for name, args in VARIANTS.items():
            with self.subTest(variant=name):
                done = run_cli(*args)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertEqual(done.stderr, "")
                check_ends_with_closing_line(self, done.stdout)

    def test_the_two_page_variant_really_has_two_pages(self):
        done = run_cli(*VARIANTS["five children, flag yes (two pages)"])
        self.assertGreaterEqual(len(done.stdout.split("\f")), 2)
        self.assertEqual(done.stdout.count(CLOSING), 1)

    def test_the_first_line_is_unchanged(self):
        for name, args in VARIANTS.items():
            with self.subTest(variant=name):
                done = run_cli(*args)
                self.assertEqual(done.stdout.split("\n")[0], FIRST)

    def test_render_report_ends_with_the_closing_line(self):
        result = guideline.compute("9500.00", "3500.00", "15", 3, "21.00", "yes")
        text = render_report(result)
        self.assertTrue(text.endswith("\n\n" + CLOSING))
        self.assertEqual(text.count(CLOSING), 1)

    def test_no_flag_turns_it_off(self):
        for flag in ("--no-closing-line", "--quiet", "--no-disclaimer"):
            with self.subTest(flag=flag):
                done = run_cli(*README_ARGS, flag)
                self.assertEqual(done.returncode, 2)
                self.assertNotIn(CLOSING, done.stdout)


if __name__ == "__main__":
    unittest.main()
