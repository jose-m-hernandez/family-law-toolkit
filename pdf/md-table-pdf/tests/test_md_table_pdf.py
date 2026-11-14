# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
import os
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import make_fixtures as fx  # noqa: E402
import md_table_pdf  # noqa: E402
from pypdf import PdfReader  # noqa: E402

TOOL = os.path.join(ROOT, "md_table_pdf.py")
PDFTOTEXT = "/opt/homebrew/bin/pdftotext"


def sq(s):
    return "".join(s.split())


def page_text(pdf, n=None):
    args = [PDFTOTEXT, "-raw"]
    if n:
        args += ["-f", str(n), "-l", str(n)]
    return subprocess.run(args + [pdf, "-"], check=True, capture_output=True,
                          text=True).stdout


class Base(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.d = self._td.name
        self.addCleanup(self._td.cleanup)

    def md(self, name, text):
        return fx.write(self.d, name, text)

    def run_tool(self, *args, cwd=None):
        return subprocess.run([sys.executable, TOOL] + list(args), cwd=cwd or self.d,
                              capture_output=True, text=True)

    def make(self, text, name="in.md", *extra):
        p = self.md(name, text)
        r = self.run_tool(p, *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return os.path.splitext(p)[0] + ".pdf", r


class TestExitCodes(Base):
    def test_01_relative_path_from_other_cwd(self):
        self.md("rel.md", fx.simple())
        os.mkdir(os.path.join(self.d, "sub"))
        r = self.run_tool("../rel.md", "-o", "../out.pdf", cwd=os.path.join(self.d, "sub"))
        self.assertEqual(r.returncode, 0, r.stderr)
        out = os.path.join(os.path.realpath(self.d), "out.pdf")
        self.assertTrue(os.path.exists(out))
        self.assertEqual(os.path.realpath(r.stdout.splitlines()[0]), out)
        self.assertIn("1 tables, 2 body rows, 1 pages", r.stdout)
        # default output: next to input
        r = self.run_tool("../rel.md", cwd=os.path.join(self.d, "sub"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.d, "rel.pdf")))

    def test_02_missing_input(self):
        self.assertEqual(self.run_tool("nope.md").returncode, 2)

    def test_03_no_table(self):
        p = self.md("nt.md", fx.no_table())
        r = self.run_tool(p)
        self.assertEqual(r.returncode, 2)
        self.assertFalse(os.path.exists(os.path.join(self.d, "nt.pdf")))

    def test_04_ragged_row_exit3_with_line(self):
        p = self.md("rag.md", fx.ragged())
        r = self.run_tool(p)
        self.assertEqual(r.returncode, 3)
        self.assertIn("rag.md:4", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.d, "rag.pdf")))

    @unittest.skipIf(os.geteuid() == 0, "root ignores permissions")
    def test_05_unwritable_output_dir(self):
        p = self.md("ok.md", fx.simple())
        ro = os.path.join(self.d, "ro")
        os.mkdir(ro)
        os.chmod(ro, stat.S_IRUSR | stat.S_IXUSR)
        self.addCleanup(os.chmod, ro, stat.S_IRWXU)
        r = self.run_tool(p, "-o", os.path.join(ro, "o.pdf"))
        self.assertEqual(r.returncode, 4)
        os.chmod(ro, stat.S_IRWXU)
        self.assertEqual(os.listdir(ro), [])
        self.assertEqual(self.run_tool(p, "-o", os.path.join(self.d, "nodir", "o.pdf")).returncode, 4)

    def test_refuses_overwrite_of_input(self):
        p = self.md("same.md", fx.simple())
        r = self.run_tool(p, "-o", p)
        self.assertEqual(r.returncode, 2)
        with open(p, encoding="utf-8") as f:
            self.assertEqual(f.read(), fx.simple())

    def test_exit5_fails_closed_no_partial(self):
        p = self.md("boom.md", fx.simple())
        orig = md_table_pdf.render
        def boom(*a, **k):
            raise RuntimeError("secret input text")
        md_table_pdf.render = boom
        try:
            import io, contextlib
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = md_table_pdf.main([p])
        finally:
            md_table_pdf.render = orig
        self.assertEqual(code, 5)
        self.assertIn("RuntimeError", err.getvalue())
        self.assertNotIn("secret", err.getvalue())
        self.assertEqual([f for f in os.listdir(self.d) if f.endswith((".pdf", ".tmp"))], [])


class TestContent(Base):
    def test_06_long_cell_wrapped_and_complete(self):
        pdf, _ = self.make(fx.long_cell())
        self.assertIn(sq(fx.LONG), sq(page_text(pdf)))

    def test_long_unbroken_token_not_clipped(self):
        # r2: a long token is no longer split. 120 X do not fit at 9 pt, so the table shrinks
        # and the token stays on one line; 300 X cannot fit even at the 6 pt floor (see test_r2_*).
        tok = "X" * 120
        pdf, _ = self.make("| A | B |\n|---|---|\n| %s | y |\n" % tok)
        self.assertIn(tok, page_text(pdf).split())

    def test_07_multipage_header_repeats_all_rows_present(self):
        pdf, r = self.make(fx.many_rows(130))
        n = len(PdfReader(pdf).pages)
        self.assertGreater(n, 2)
        self.assertIn("130 body rows", r.stdout)
        for i in range(1, n + 1):
            self.assertIn("NoVesselRemark", sq(page_text(pdf, i)), "page %d" % i)
        full = sq(page_text(pdf))
        for i in range(130):
            self.assertIn("R%04d" % i, full)
            self.assertIn("VesselAlder-%d" % i, full)
            self.assertIn("remarkuniq%04dforrow%d" % (i, i), full)

    def test_08_landscape(self):
        pdf, _ = self.make(fx.simple())
        for pg in PdfReader(pdf).pages:
            self.assertGreater(float(pg.mediabox.width), float(pg.mediabox.height))
            self.assertAlmostEqual(float(pg.mediabox.width), 792, delta=1)

    def test_09_page_x_of_y(self):
        pdf, r = self.make(fx.many_rows(130))
        n = len(PdfReader(pdf).pages)
        self.assertIn("%d pages" % n, r.stdout)
        self.assertIn(sq("page %d of %d" % (n, n)), sq(page_text(pdf, n)))
        self.assertIn(sq("page 1 of %d" % n), sq(page_text(pdf, 1)))

    def test_10_escaped_pipes(self):
        pdf, _ = self.make(fx.escaped_pipes())
        t = " ".join(page_text(pdf).split())
        self.assertIn("a | b", t)
        self.assertIn("either a or b", t)

    def test_11_non_ascii_survives(self):
        pdf, _ = self.make(fx.non_ascii())
        t = " ".join(page_text(pdf).split())
        for s in ["Zoë Núñez", "café", "“quoted”", "—",
                  "naïve", "façade"]:
            self.assertIn(s, t)

    def test_11b_unsupported_chars_fail_loudly(self):
        p = self.md("cjk.md", fx.unsupported())
        r = self.run_tool(p)
        self.assertEqual(r.returncode, 3)
        self.assertIn("cjk.md:3", r.stderr)
        self.assertIn("U+1F600", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.d, "cjk.pdf")))

    def test_bold_code_rendered_markers_gone_title_and_headings(self):
        pdf, _ = self.make(fx.simple(), "in.md", "--title", "Trial Prep Binder", "--markup")
        t = " ".join(page_text(pdf).split())
        self.assertIn("fragile item", t)
        self.assertNotIn("**", t)
        self.assertNotIn("`", t)
        self.assertIn("Trial Prep Binder", t)
        self.assertIn("Exhibit A", t)
        self.assertIn("Intro paragraph about the Willow Creek Exhibit.", t)

    def test_literal_default_keeps_markers(self):
        pdf, _ = self.make(fx.simple())
        t = " ".join(page_text(pdf).split())
        self.assertIn("**fragile** item", t)
        self.assertIn("`kettle`", t)

    def test_multiple_tables_summary(self):
        _, r = self.make(fx.simple() + "\n## Two\n\n" + fx.escaped_pipes())
        self.assertIn("2 tables, 3 body rows", r.stdout)


if __name__ == "__main__":
    unittest.main()
