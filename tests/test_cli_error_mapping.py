# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""The CLI turns parameter names in error messages into flags, and only the ones meant as names."""

import contextlib
import io
import unittest
from unittest import mock

from family_law_toolkit.support import __main__ as cli_main
from family_law_toolkit.support.guideline import compute

PREFIX = "python3 -m family_law_toolkit.support: error: "


def base_flags(**overrides):
    """The valid base flags, with any flag's value(s) replaced; a list value repeats the flag."""
    flags = {
        "--a-ndi": ["6000.00"],
        "--b-ndi": ["2000.00"],
        "--a-time-percent": ["35"],
        "--children": ["2"],
        "--minimum-wage-hourly": ["21.00"],
    }
    for flag, value in overrides.items():
        flags["--" + flag.replace("_", "-")] = value if isinstance(value, list) else [value]
    argv = []
    for flag, values in flags.items():
        for value in values:
            argv.extend([flag, value])
    return argv


def run_main(argv, **patches):
    """Call main in-process; return (exit code, stdout, stderr)."""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        if patches:
            with mock.patch.object(cli_main, "compute", **patches):
                code = cli_main.main(argv)
        else:
            code = cli_main.main(argv)
    return code, out.getvalue(), err.getvalue()


class CliErrorMappingTests(unittest.TestCase):
    def assert_one_error_line(self, argv, expected_text, **patches):
        code, out, err = run_main(argv, **patches)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertEqual(err, PREFIX + expected_text + "\n")
        self.assertEqual(len(err.splitlines()), 1)

    def test_every_current_error_line_is_pinned(self):
        rows = [
            (base_flags(a_ndi="1,000"), "--a-ndi is not a decimal number"),
            (base_flags(a_ndi="NaN"), "--a-ndi must be a finite number"),
            (base_flags(a_ndi="4000.001"), "--a-ndi has more than 2 decimals"),
            (base_flags(a_ndi="1E+30"), "--a-ndi is too large"),
            (base_flags(b_ndi="-0.01"), "--b-ndi must not be negative"),
            (
                base_flags(a_time_percent="100.01"),
                "--a-time-percent must be between 0 and 100",
            ),
            (base_flags(children="11"), "--children must be between 1 and 10"),
            (
                base_flags(minimum_wage_hourly="0"),
                "--minimum-wage-hourly must be greater than zero",
            ),
            (
                base_flags(a_time_percent=["30", "100.01"]),
                "--a-time-percent must be between 0 and 100",
            ),
            (
                base_flags(a_time_percent=["30", "40"])
                + ["--same-time-sharing-arrangement", "yes"],
                "--a-time-percent gives different percentages per child, and "
                "--same-time-sharing-arrangement is yes: the two inputs "
                "contradict each other",
            ),
            (
                base_flags(a_time_percent=["30", "40", "50"]),
                "--a-time-percent needs one percentage per child: the number of "
                "percentages differs from --children",
            ),
        ]
        for argv, text in rows:
            with self.subTest(text=text):
                self.assert_one_error_line(argv, text)

        # Two messages that argv cannot reach: take the real exception, hand it to main.
        with self.assertRaises(ValueError) as maybe:
            compute(
                "6000.00", "2000.00", "35", 2, "21.00",
                same_time_sharing_arrangement="maybe",
            )
        with self.assertRaises(ValueError) as not_string:
            compute(6000, "2000.00", "35", 2, "21.00")
        unreachable = [
            (maybe.exception, "--same-time-sharing-arrangement must be yes or no"),
            (not_string.exception, "--a-ndi must be a decimal string"),
        ]
        for error, text in unreachable:
            with self.subTest(text=text):
                self.assert_one_error_line(base_flags(), text, side_effect=error)

    def test_an_ordinary_word_that_matches_a_parameter_name_is_not_rewritten(self):
        # Today's all-words mapper would rewrite "children" in both messages.
        class Named(ValueError):
            def __init__(self, message, names):
                ValueError.__init__(self, message)
                self.names = tuple(names)

        with self.subTest(kind="plain ValueError"):
            self.assert_one_error_line(
                base_flags(),
                "--a-ndi must be at most the amount for all the children combined",
                side_effect=ValueError(
                    "a_ndi must be at most the amount for all the children combined"
                ),
            )
        with self.subTest(kind="named ValueError"):
            self.assert_one_error_line(
                base_flags(),
                "--a-time-percent counts the children once each",
                side_effect=Named(
                    "a_time_percent counts the children once each", ("a_time_percent",)
                ),
            )

    def test_named_messages_use_each_declared_name_exactly_once(self):
        with self.assertRaises(ValueError) as contradiction:
            compute(
                "6000.00", "2000.00", ["30", "40"], 2, "21.00",
                same_time_sharing_arrangement="yes",
            )
        with self.assertRaises(ValueError) as count:
            compute("6000.00", "2000.00", ["30", "40", "50"], 2, "21.00")
        for label, error in (("contradiction", contradiction.exception), ("count", count.exception)):
            with self.subTest(error=label):
                self.assertTrue(hasattr(error, "names"))
                words = str(error).split(" ")
                for name in error.names:
                    self.assertEqual(words.count(name), 1)
                for word in words:
                    if word in cli_main._FLAG_FOR_NAME:
                        self.assertIn(word, error.names)


if __name__ == "__main__":
    unittest.main()
