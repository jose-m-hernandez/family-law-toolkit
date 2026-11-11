# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""The compare command (spec sections 3, 5.1 and 7): usage, files, order of checks, streams,
exit status. Most cases run the command in a subprocess, with bytes out."""

import ast
import errno
import os
import subprocess
import sys
import time
import unittest
from unittest import mock

from family_law_toolkit.compare import __main__ as cli_main
from family_law_toolkit.compare import differences, report
from tests.compare_support import (
    FIXTURES, PA, PB, PREFIX, ROOT, USAGE_END, FakeStream, Workdir, render, run_cli,
    run_main, spec_help,
)

REFUSED = "is not a plain-text file; this version reads plain text and Markdown only"


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self.work = Workdir()
        self.addCleanup(self.work.cleanup)
        self.good = "good.txt"
        self.work.write(self.good, PA + "\n")
        self.other = "other.txt"
        self.work.write(self.other, PB + "\n")

    def run_cli(self, *args):
        return run_cli(args, self.work.path)

    def assert_error(self, args, message, ending=""):
        done = self.run_cli(*args)
        self.assertEqual((done.returncode, done.stdout), (2, b""), args)
        self.assertEqual(done.stderr.count(b"\n"), 1, args)
        self.assertEqual(done.stderr, (PREFIX + message + ending + "\n").encode("utf-8"), args)

    def assert_usage_error(self, args):
        done = self.run_cli(*args)
        self.assertEqual((done.returncode, done.stdout), (2, b""), args)
        self.assertEqual(done.stderr.count(b"\n"), 1, args)
        self.assertTrue(done.stderr.startswith(PREFIX.encode()), args)
        self.assertTrue(done.stderr.endswith(USAGE_END.encode() + b"\n"), args)
        return done.stderr.decode("utf-8")

    def argv(self, side, value):
        """--old/--new arguments with value on `side` and a valid file on the other."""
        if side == "old":
            return ["--old", value, "--new", self.other]
        return ["--old", self.good, "--new", value]


class CommandTests(CliTestCase):
    def test_t01_identical_bytes(self):
        self.work.write("copy.txt", PA + "\n")
        done = self.run_cli("--old", self.good, "--new", "copy.txt")
        self.assertEqual((done.returncode, done.stderr), (0, b""))
        lines = done.stdout.decode("utf-8").split("\n")
        self.assertIn("Result: the two files are identical, byte for byte.", lines)
        self.assertNotIn("Differences", lines)
        self.assertEqual(done.stdout, render(PA + "\n", PA + "\n", self.good, "copy.txt").encode("utf-8"))

    def test_rows_exit_1_through_the_command(self):
        for key, (old, new) in FIXTURES.items():
            with self.subTest(key):
                work = Workdir()
                self.addCleanup(work.cleanup)
                work.write("old.txt", old)
                work.write("new.txt", new)
                done = run_cli(["--old", "old.txt", "--new", "new.txt"], work.path)
                self.assertEqual((done.returncode, done.stderr), (1, b""))
                self.assertEqual(done.stdout, render(old, new, "old.txt", "new.txt").encode("utf-8"))
                self.assertTrue(done.stdout.endswith(b"\n"))

    def test_t19_escaping_on_standard_error(self):
        self.assert_error(["--old", "a\nb.txt", "--new", self.good], "cannot read --old a<U+000A>b.txt: no such file")
        done = self.run_cli(b"--old", b"\xff.txt", "--new", self.good)
        self.assertEqual((done.returncode, done.stdout, done.stderr.count(b"\n")), (2, b"", 1))
        line = done.stderr.decode("utf-8")
        self.assertTrue(line.startswith(PREFIX + "cannot read --old <U+DCFF>.txt: "), line)
        self.assertTrue(line.endswith((": no such file\n", ": it could not be read\n")), line)
        line = self.assert_usage_error(["--old", self.good, "--new", self.other, "--bo\ngus\x1b"])
        self.assertIn("<U+000A>gus<U+001B>", line)
        self.assertNotIn("\x1b", line)

    def test_t21_cannot_run_cases(self):
        os.mkdir(os.path.join(self.work.path, "sub"))
        os.mkfifo(os.path.join(self.work.path, "pipe"))
        self.work.write("big.txt", b"a" * 200001)
        for name, data in (("nul.txt", b"a\x00b"), ("pdf.txt", b"%PDF-1.4 a"), ("zip.txt", b"PK\x03\x04a"),
                           ("bom_pdf.txt", b"\xef\xbb\xbf%PDF-"), ("bad.txt", b"a\xff"), ("empty.txt", b""),
                           ("bom.txt", b"\xef\xbb\xbf"), ("space.txt", b" \n\t\x0b\xe2\x80\x83")):
            self.work.write(name, data)
        for suffix in (".pdf", ".docx", ".doc", ".rtf", ".odt", ".PDF", ".DocX"):
            self.work.write("draft" + suffix, PA)
        for side in ("old", "new"):
            flag = "--" + side
            rows = [
                ("missing.txt", "cannot read %s missing.txt: no such file" % flag),
                ("sub", "cannot read %s sub: it is a folder" % flag),
                ("/dev/null", "cannot read %s /dev/null: it is not a regular file" % flag),
                ("pipe", "cannot read %s pipe: it is not a regular file" % flag),
                ("big.txt", "%s big.txt is larger than 200,000 bytes" % flag),
                ("nul.txt", "%s nul.txt %s" % (flag, REFUSED)),
                ("pdf.txt", "%s pdf.txt %s" % (flag, REFUSED)),
                ("zip.txt", "%s zip.txt %s" % (flag, REFUSED)),
                ("bom_pdf.txt", "%s bom_pdf.txt %s" % (flag, REFUSED)),
                ("bad.txt", "%s bad.txt cannot be read as UTF-8" % flag),
                ("empty.txt", "%s empty.txt has no text to compare" % flag),
                ("bom.txt", "%s bom.txt has no text to compare" % flag),
                ("space.txt", "%s space.txt has no text to compare" % flag),
            ]
            for suffix in (".pdf", ".docx", ".doc", ".rtf", ".odt", ".PDF", ".DocX"):
                rows.append(("draft" + suffix, "%s draft%s %s" % (flag, suffix, REFUSED)))
            for value, message in rows:
                with self.subTest(side=side, value=value):
                    self.assert_error(self.argv(side, value), message)
        self.assert_error(["--old", self.good, "--new", self.good], "--old and --new name the same file")
        os.symlink(self.good, os.path.join(self.work.path, "link.txt"))
        self.assert_error(["--old", self.good, "--new", "link.txt"], "--old and --new name the same file")
        os.link(os.path.join(self.work.path, self.good), os.path.join(self.work.path, "hard.txt"))
        self.assert_error(["--new", self.good, "--old", "hard.txt"], "--old and --new name the same file")
        self.work.write("many_old.txt", "\n\n".join("old %d" % n for n in range(501)))
        self.work.write("many_new.txt", "\n\n".join("new %d" % n for n in range(500)))
        self.assert_error(["--old", "many_old.txt", "--new", "many_new.txt"],
                          "too many paragraphs lie between the first and last differences to compare "
                          "within this tool's limit")
        for side in ("old", "new"):
            self.assert_error(["--" + side + "=./-x.txt"] + ["--" + ("new" if side == "old" else "old"), self.good],
                              "cannot read --%s ./-x.txt: no such file" % side)

    def test_t21_usage_errors(self):
        for args in ([], ["--old", self.good], ["--new", self.good], ["--old", self.good, "--new", self.other, "x"],
                     ["--old", self.good, "--new", self.other, "--bogus"], ["--ol", self.good, "--new", self.other],
                     ["--old"], ["--old", self.good, "--new"], ["--old", "--new", self.good]):
            with self.subTest(args=args):
                self.assert_usage_error(args)
        for side, other in (("old", "new"), ("new", "old")):
            self.assert_error(["--%s" % side, self.good, "--%s" % side, self.good, "--%s" % other, self.other],
                              "--%s was given more than once" % side, USAGE_END)
            self.assert_error(["--%s" % side, "-", "--%s" % other, self.other],
                              "--%s cannot be -" % side, USAGE_END)

    @unittest.skipIf(os.geteuid() == 0, "running as root: permission bits are not enforced")
    def test_t21_permission_denied(self):
        locked = self.work.write("locked.txt", PA)
        os.chmod(locked, 0)
        self.addCleanup(os.chmod, locked, 0o600)
        for side in ("old", "new"):
            self.assert_error(self.argv(side, "locked.txt"), "cannot read --%s locked.txt: permission denied" % side)

    def test_t21_could_not_be_read(self):
        error = OSError(errno.EIO, "Input/output error")
        with mock.patch.object(cli_main, "open", create=True, side_effect=error):
            code, out, err = run_main(["--old", os.path.join(self.work.path, self.good),
                                       "--new", os.path.join(self.work.path, self.other)])
        self.assertEqual((code, out), (2, b""))
        self.assertEqual(err.decode(), PREFIX + "cannot read --old %s: it could not be read\n"
                         % os.path.join(self.work.path, self.good))

    def test_t21_check_order(self):
        for name, data in (("nul.txt", b"a\x00b"), ("empty.txt", b""), ("bad.txt", b"\xff"), ("both.txt", b"\xff\x00"),
                           ("draft.pdf", PA), ("big.pdf", b"a" * 200001)):
            self.work.write(name, data)
        order = [
            # usage first, then --old rows 2 to 4, then --new rows 2 to 4
            (["--old", "missing.txt"], None),
            (["--old", "missing.txt", "--new", "missing2.txt"], "cannot read --old missing.txt: no such file"),
            (["--old", "draft.pdf", "--new", "missing.txt"], "--old draft.pdf " + REFUSED),
            (["--old", "missing.txt", "--new", "draft.pdf"], "cannot read --old missing.txt: no such file"),
            (["--old", "big.pdf", "--new", "missing.txt"], "--old big.pdf is larger than 200,000 bytes"),
            (["--old", "draft.pdf", "--new", "draft.pdf"], "--old draft.pdf " + REFUSED),
            # row 5 after rows 2 to 4 of both files, before rows 6 to 8
            (["--old", "nul.txt", "--new", "missing.txt"], "cannot read --new missing.txt: no such file"),
            (["--old", "nul.txt", "--new", "nul.txt"], "--old and --new name the same file"),
            # rows 6 to 8 for --old, then for --new, within one file in table order
            (["--old", "empty.txt", "--new", "nul.txt"], "--old empty.txt has no text to compare"),
            (["--old", "bad.txt", "--new", "nul.txt"], "--old bad.txt cannot be read as UTF-8"),
            (["--old", "both.txt", "--new", "empty.txt"], "--old both.txt " + REFUSED),
            (["--old", self.good, "--new", "bad.txt"], "--new bad.txt cannot be read as UTF-8"),
        ]
        for args, message in order:
            with self.subTest(args=args):
                if message is None:
                    self.assert_usage_error(args)
                else:
                    self.assert_error(args, message)

    def test_t22_help(self):
        expected = (spec_help() + "\n").encode("utf-8")
        for args in (["--help"], ["-h"], ["--old", "missing.txt", "--bogus", "--help"], ["x", "-h", "--new"],
                     ["--old", "-", "--old", "-", "-h"]):
            with self.subTest(args=args):
                done = self.run_cli(*args)
                self.assertEqual((done.returncode, done.stdout, done.stderr), (0, expected, b""))

    def test_t23_output_failures(self):
        args = ["--old", os.path.join(self.work.path, self.good), "--new", os.path.join(self.work.path, self.other)]
        text = render(PA + "\n", PB + "\n", args[1], args[3]).encode("utf-8")
        line = PREFIX + "cannot write output\n"
        # standard output closed before the command starts
        env = dict(os.environ, PYTHONPATH=str(ROOT))
        done = subprocess.run(["sh", "-c", 'exec "$0" "$@" >&-', sys.executable, "-m", "family_law_toolkit.compare"]
                              + args, cwd=self.work.path, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=60)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (2, b"", line.encode()))
        # no standard output at all, in the command and for the help
        for argv in (args, ["--help"]):
            err = FakeStream()
            with mock.patch.object(sys, "stdout", None), mock.patch.object(sys, "stderr", err):
                self.assertEqual(cli_main.main(argv), 2)
            self.assertEqual(err.value(), line.encode())
        # a write that fails before any byte goes out, and one that fails after part has
        code, out, err = run_main(args, stdout=FakeStream(fail_after_bytes=0))
        self.assertEqual((code, out, err), (2, b"", line.encode()))
        code, out, err = run_main(args, stdout=FakeStream(fail_after_bytes=25))
        self.assertEqual((code, out, err), (2, text[:25], line.encode()))
        # a failure inside the comparison and inside the report: one line, no traceback
        for target, name in ((differences, "compare"), (report, "render_report"), (differences, "check")):
            for failure in (RuntimeError("boom"), MemoryError()):
                with self.subTest(name=name, failure=failure), mock.patch.object(target, name, side_effect=failure):
                    code, out, err = run_main(args)
                self.assertEqual((code, out), (2, b""))
                self.assertEqual(err, (PREFIX + "internal error; the comparison did not finish\n").encode())
        # a real broken pipe: the reader goes away before the command writes
        process = subprocess.Popen([sys.executable, "-m", "family_law_toolkit.compare"] + args, cwd=self.work.path,
                                   env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.stdout.close()
        stderr = process.stderr.read()
        process.stderr.close()
        self.assertEqual(process.wait(timeout=60), 2)
        self.assertEqual(stderr, line.encode())

    def test_t25_relative_path_as_typed(self):
        first = self.run_cli("--old", "./" + self.good, "--new", "../" + os.path.basename(self.work.path) + "/" + self.other)
        again = self.run_cli("--old", "./" + self.good, "--new", "../" + os.path.basename(self.work.path) + "/" + self.other)
        self.assertEqual(first.returncode, 1)
        self.assertEqual(first.stdout, again.stdout)
        lines = first.stdout.decode().split("\n")
        self.assertIn("  Old (--old): ./good.txt", lines)
        self.assertIn("  New (--new): ../%s/other.txt" % os.path.basename(self.work.path), lines)
        self.assertNotIn(os.path.realpath(self.work.path).encode(), first.stdout)

    def test_t26_imports(self):
        allowed = {"argparse", "collections", "difflib", "errno", "hashlib", "os", "re", "stat", "sys",
                   "textwrap", "unicodedata", "family_law_toolkit"}
        barred = {"socket", "ssl", "http", "urllib", "ftplib", "smtplib"}

        def imported(source):
            names = set()
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Import):
                    names |= {alias.name.split(".")[0] for alias in node.names}
                elif isinstance(node, ast.ImportFrom):
                    self.assertEqual(node.level, 0)
                    names.add(node.module.split(".")[0])
            return names

        files = sorted((ROOT / "family_law_toolkit" / "compare").glob("*.py"))
        self.assertEqual([f.name for f in files], ["__init__.py", "__main__.py", "differences.py", "report.py"])
        for path in files:
            with self.subTest(path.name):
                names = imported(path.read_text(encoding="utf-8"))
                self.assertEqual(names - allowed, set())
                self.assertEqual(names & barred, set())
        # positive control: the check catches an import the package must not have
        self.assertEqual(imported("def f():\n    import urllib.request\n") - allowed, {"urllib"})

    def test_t28_file_size_limit(self):
        words = "a " * 100000
        self.assertEqual(len(words.encode()), 200000)
        edited = "a " * 50000 + "b " + "a " * 49999
        self.work.write("max_old.txt", words)
        self.work.write("max_new.txt", edited)
        started = time.monotonic()
        done = self.run_cli("--old", "max_old.txt", "--new", "max_new.txt")
        self.assertLess(time.monotonic() - started, 10)
        self.assertEqual((done.returncode, done.stderr), (1, b""))
        self.assertEqual(sum(1 for l in done.stdout.decode().split("\n") if l.startswith("     - ")), 1)
        self.assertIn(b'old "a", new "b", after "a a a"', done.stdout)
        self.work.write("over_old.txt", words + "a")
        self.assert_error(["--old", "over_old.txt", "--new", "max_new.txt"], "--old over_old.txt is larger than 200,000 bytes")
        self.assert_error(["--old", "max_old.txt", "--new", "over_old.txt"], "--new over_old.txt is larger than 200,000 bytes")


if __name__ == "__main__":
    unittest.main()
