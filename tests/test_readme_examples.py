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
