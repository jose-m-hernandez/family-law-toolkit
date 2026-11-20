# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""The README's two printed example reports equal what the commands print."""

import subprocess
import sys
import unittest
from pathlib import Path

from tests.test_report import run_cli

ROOT = Path(__file__).resolve().parent.parent
INDENT = "    "
SUPPORT_COMMAND = (
    INDENT + "python3 -m family_law_toolkit.support --a-ndi 9500.00 --b-ndi 3500.00"
    " --a-time-percent 15 --children 3 --minimum-wage-hourly 21.00"
)
# The additional-costs example. It starts with a prompt so that the line that
# runs the first example (test_report.test_readme_example_command_runs) stays
# the only README line that begins with the bare command.
ADDITIONAL_COMMAND = (
    INDENT + "$ python3 -m family_law_toolkit.support --a-ndi 5000.00 --b-ndi 3000.00"
    " --a-time-percent 20 --children 1 --minimum-wage-hourly 21.00"
    " --childcare-monthly 600.00 --uninsured-health-monthly 120.00"
    " --a-adjusted-ndi 5000.00 --b-adjusted-ndi 3000.00"
)
COMPARE_COMMAND = (
    INDENT + "python3 -m family_law_toolkit.compare"
    " --old docs/examples/letter-a.txt --new docs/examples/letter-b.txt"
)


def readme_lines():
    return (ROOT / "README.md").read_text(encoding="utf-8").split("\n")


def block_after(command_line):
    """The indented block that follows the one line equal to command_line.

    The block starts at the first indented line after the command and runs to
    the next blank line that is followed by an unindented line.
    """
    lines = readme_lines()
    if lines.count(command_line) != 1:
        raise AssertionError("README must hold the command line exactly once")
    i = lines.index(command_line) + 1
    while i < len(lines) and not lines[i].startswith(INDENT):
        i += 1
    block = []
    while i < len(lines):
        line = lines[i]
        if line == "":
            following = lines[i + 1] if i + 1 < len(lines) else ""
            if not following.startswith(INDENT):
                break
        elif not line.startswith(INDENT):
            break
        block.append(line[len(INDENT):] if line else "")
        i += 1
    if not block:
        raise AssertionError("README holds no output block after the command")
    return "\n".join(block) + "\n"


class ReadmeExampleTests(unittest.TestCase):
    def test_support_example_output_is_what_the_command_prints(self):
        args = SUPPORT_COMMAND.split("family_law_toolkit.support ")[1].split()
        done = run_cli(*args)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stderr, "")
        self.assertEqual(block_after(SUPPORT_COMMAND), done.stdout)

    def test_additional_costs_example_section_is_what_the_command_prints(self):
        args = ADDITIONAL_COMMAND.split("family_law_toolkit.support ")[1].split()
        done = run_cli(*args)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stderr, "")
        shown = block_after(ADDITIONAL_COMMAND).rstrip("\n").split("\n")
        printed = done.stdout.split("\n")
        self.assertEqual(shown[0], "Additional child support (FC 4062), split under FC 4061")
        self.assertEqual(len(shown), 14)
        start = printed.index(shown[0])
        # The README shows the section whole, line for line, as printed.
        self.assertEqual(printed[start:start + len(shown)], shown)
        # And the section ends where the README's block ends.
        self.assertEqual(printed[start + len(shown)], "")

    def test_compare_example_exits_1_and_output_is_what_the_command_prints(self):
        args = COMPARE_COMMAND.split("family_law_toolkit.compare ")[1].split()
        done = subprocess.run(
            [sys.executable, "-m", "family_law_toolkit.compare", *args],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60,
        )
        self.assertEqual(done.returncode, 1)
        self.assertEqual(done.stderr, "")
        self.assertEqual(block_after(COMPARE_COMMAND), done.stdout)


if __name__ == "__main__":
    unittest.main()
