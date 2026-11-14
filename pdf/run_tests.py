#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Run the unit tests of each PDF tool suite, and fail if a suite finds none.

Usage: python3 pdf/run_tests.py [SUITE_DIR ...]

With no arguments the suites are page-render and md-table-pdf, found next to
this script. Each argument is a directory that holds a tests/ folder and
replaces the defaults. Each suite runs in a child process whose working
directory is the suite folder, as `python3 -m unittest discover -s tests` would.
Exit status: 0 if every suite collected at least one test and passed, else 1.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SUITES = ("page-render", "md-table-pdf")

CHILD = """
import sys
import unittest

suite = unittest.defaultTestLoader.discover("tests")
count = suite.countTestCases()
if count == 0:
    print("no tests collected")
    sys.exit(5)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
"""


def count_run(output):
    """Return N from the 'Ran N test(s)' line of the child's output, or 0."""
    for line in output.splitlines():
        if line.startswith("Ran "):
            parts = line.split()
            if len(parts) > 1 and parts[1].isdigit():
                return int(parts[1])
    return 0


def run_suite(folder):
    name = os.path.basename(os.path.normpath(folder))
    proc = subprocess.run(
        [sys.executable, "-c", CHILD],
        cwd=folder,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stdout.flush()
    tests = count_run(proc.stdout)
    if proc.returncode == 0:
        print("%s: %d tests, OK" % (name, tests))
        return tests, True
    if proc.returncode == 5 and "no tests collected" in proc.stdout:
        print("%s: 0 tests, NO TESTS" % name)
        return 0, False
    print("%s: %d tests, FAILED" % (name, tests))
    return tests, False


def main(argv):
    if argv:
        folders = [os.path.abspath(a) for a in argv]
    else:
        folders = [os.path.join(HERE, s) for s in DEFAULT_SUITES]
    total = 0
    all_ok = True
    for folder in folders:
        tests, ok = run_suite(folder)
        total += tests
        all_ok = all_ok and ok
    print("pdf tests: %d suites, %d tests, %s"
          % (len(folders), total, "OK" if all_ok else "FAILED"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
