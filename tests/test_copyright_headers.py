# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Every tracked Python file starts with the licence and copyright lines,
after an optional shebang and an optional encoding line."""

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = [
    "# SPDX-License-Identifier: AGPL-3.0-or-later",
    "# Copyright (C) 2026 Jose Miguel Hernandez",
]
ENCODING = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*[-\w.]+")


def tracked_python_files():
    out = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout
    return sorted(out.split("\n")[:-1]) if out else []


def header_ok(text):
    lines = text.split("\n")
    i = 0
    if lines and lines[0].startswith("#!"):
        i = 1
    if len(lines) > i and ENCODING.match(lines[i]):
        i += 1
    return lines[i:i + 2] == HEADER


class CopyrightHeaders(unittest.TestCase):
    def test_there_are_files_to_check(self):
        self.assertTrue(tracked_python_files())

    def test_every_python_file_has_the_header(self):
        bad = [
            f for f in tracked_python_files()
            if not header_ok((ROOT / f).read_text(encoding="utf-8"))
        ]
        self.assertEqual(bad, [], "missing licence/copyright header")

    def test_checker_accepts_shebang_and_encoding_lines(self):
        body = "\n".join(HEADER) + "\nx = 1\n"
        self.assertTrue(header_ok(body))
        self.assertTrue(header_ok("#!/usr/bin/env python3\n" + body))
        self.assertTrue(header_ok("# -*- coding: utf-8 -*-\n" + body))
        self.assertTrue(header_ok("#!/usr/bin/env python3\n# coding: utf-8\n" + body))

    def test_checker_rejects_a_missing_or_late_header(self):
        self.assertFalse(header_ok("x = 1\n"))
        self.assertFalse(header_ok(HEADER[0] + "\nx = 1\n"))
        self.assertFalse(header_ok("x = 1\n" + "\n".join(HEADER) + "\n"))


if __name__ == "__main__":
    unittest.main()
