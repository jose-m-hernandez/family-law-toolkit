# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Fix-round tests. Inputs reuse the shared fixtures."""
import contextlib
import copy
import io
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_md_table_pdf import Base, page_text, PDFTOTEXT  # noqa: E402
import md_table_pdf as m  # noqa: E402

STARS = ("| Acct | Note |\n|---|---|\n| *****1234 | masked |\n"
         "| ****1234 / ****5678 | two accounts |\n| 2**10 and 3**2 | powers |\n"
         "| p < .05** | sig |\n")
B2B = "| A | B |\n|---|---|\n| 1 | 2 |\n| C | D |\n|---|---|\n| 3 | 4 |\n"
BLANK = "| A | B |\n|---|---|\n| 1 | 2 |\n\n| 3 | 4 |\n| 5 | 6 |\n"
NOPIPE = "No | Entry\n---|---\n#11 | Motion\n12 | Order\n13 | Ruling\n"
ONECOL = "| Exhibits |\n|---|\n| Ex 1 |\nTotal pages: 40\n"
HEADING = "# Item C#\n\n## Foo ##\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"


def flat(pdf):
    return " ".join(page_text(pdf).split())


def bbox(pdf):
    out = subprocess.run([PDFTOTEXT, "-bbox", pdf, "-"], check=True,
                         capture_output=True, text=True).stdout
    words = {}
    for x0, x1, w in re.findall(r'xMin="([\d.]+)" yMin="[\d.]+" xMax="([\d.]+)" yMax="[\d.]+">([^<]*)<', out):
        words.setdefault(w, (float(x0), float(x1)))
    return words


class TestLiteral(Base):
    def test_fix1_literal_default(self):
        pdf, _ = self.make(STARS)
        t = flat(pdf)
        for s in ["*****1234", "****1234 / ****5678", "2**10 and 3**2", "p < .05**"]:
            self.assertIn(s, t)

    def test_fix1_markup_flag_renders_bold_code(self):
        pdf, _ = self.make("| A | B |\n|---|---|\n| **fragile** item | `kettle` x |\n",
                           "in.md", "--markup")
        t = flat(pdf)
        self.assertIn("fragile item", t)
        self.assertIn("kettle x", t)
        self.assertNotIn("**", t)
        self.assertNotIn("`", t)

    def test_fix1_markup_flanking(self):
        md = ("| A | B |\n|---|---|\n| *****1234 | ****1234 / ****5678 |\n"
              "| p < .05** | a ** b ** c |\n| **!!** | ** x** |\n| 2**10 and 3**2 | z |\n")
        pdf, _ = self.make(md, "in.md", "--markup")
        t = flat(pdf)
        for s in ["*****1234", "****1234 / ****5678", "p < .05**", "a ** b ** c",
                  "**!!**", "** x**"]:
            self.assertIn(s, t)
        self.assertIn("210 and 32", t)  # flanked and alphanumeric: bold, markers removed

    def test_fix1_literal_selfcheck_intends_raw_text(self):
        # in literal mode a blanked cell holding '**x**' must be caught against the raw text
        blocks = m.parse("| A |\n|---|\n| **x** |\n", "x")
        b2 = copy.deepcopy(blocks)
        b2[0][2][0][0] = ""
        data, pages, _, _ = m.render(b2, None, 9)
        with self.assertRaises(m.ToolError) as cm:
            m.verify(data, blocks, pages)
        self.assertEqual(cm.exception.code, 5)


class TestStructure(Base):
    def test_fix2_back_to_back_tables(self):
        r = self.run_tool(self.md("b2b.md", B2B))
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("b2b.md:5", r.stderr)
        self.assertIn("separator row inside a table", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.d, "b2b.pdf")))

    def test_fix3_blank_line_inside_table(self):
        r = self.run_tool(self.md("blank.md", BLANK))
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("blank.md:5", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.d, "blank.pdf")))

    def test_fix3_pipe_line_without_header(self):
        r = self.run_tool(self.md("nh.md", "| A | B |\n|---|---|\n| 1 | 2 |\n\nText\n\n| x | y |\n"))
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("nh.md:7", r.stderr)

    def test_fix4_no_outer_pipes_hash_row(self):
        pdf, r = self.make(NOPIPE)
        self.assertIn("1 tables, 3 body rows", r.stdout)
        t = flat(pdf)
        self.assertIn("#11", t)
        self.assertIn("Ruling", t)

    def test_fix5_one_column_ends_at_pipeless_line(self):
        pdf, r = self.make(ONECOL)
        self.assertIn("1 tables, 1 body rows", r.stdout)
        self.assertIn("Total pages: 40", flat(pdf))

    def test_fix6_heading_closing_hashes(self):
        pdf, _ = self.make(HEADING)
        t = flat(pdf)
        self.assertIn("Item C#", t)
        self.assertIn("Foo", t)
        self.assertNotIn("Foo ##", t)


def drop_case(md, r, c, markup=False):
    blocks = m.parse(md, "x")
    b2 = copy.deepcopy(blocks)
    t = [b for b in b2 if b[0] == "t"][0]
    rows = [t[1]] + t[2]
    rows[r][c] = ""
    return blocks, b2


class TestSelfCheck(Base):
    CASES = {
        "footer_digit": ("| Count | Item |\n|---|---|\n| 1 | widget |\n", 1, 0),
        "header_word": ("| Paid | Status |\n|---|---|\n| x | Paid |\n", 1, 1),
        "substring": ("| Amt | Ref |\n|---|---|\n| 100 | a |\n| 10 | b |\n", 2, 0),
        "paragraph": ("Defendant denies.\n\n| Party | Pos |\n|---|---|\n| Defendant | denies |\n", 1, 0),
        "concat": ("| A | B | C |\n|---|---|---|\n| 1 | 2 | x |\n| 12 | y | z |\n", 2, 0),
        "multipage_header_word": (
            "| Paid | Note |\n|---|---|\n" + "".join("| r%d | n%d |\n" % (i, i) for i in range(80))
            + "| Paid | last |\n", 81, 0),
    }

    def test_fix7_dropped_cell_caught(self):
        for name, (md, r, c) in self.CASES.items():
            with self.subTest(name):
                blocks, b2 = drop_case(md, r, c)
                data, pages, _, _ = m.render(b2, None, 9)
                with self.assertRaises(m.ToolError) as cm:
                    m.verify(data, blocks, pages)
                self.assertEqual(cm.exception.code, 5)

    def test_fix7_cli_exit5_no_file(self):
        for name, (md, r, c) in self.CASES.items():
            with self.subTest(name):
                p = self.md(name + ".md", md)
                orig = m.render

                def dropping(blocks, title, fs, *a, **k):
                    b2 = copy.deepcopy(blocks)
                    t = [b for b in b2 if b[0] == "t"][0]
                    ([t[1]] + t[2])[r][c] = ""
                    return orig(b2, title, fs, *a, **k)
                m.render = dropping
                try:
                    with contextlib.redirect_stderr(io.StringIO()):
                        code = m.main([p])
                finally:
                    m.render = orig
                self.assertEqual(code, 5)
                self.assertFalse(os.path.exists(os.path.join(self.d, name + ".pdf")))

    def test_fix7_intact_documents_pass(self):
        for name, (md, r, c) in self.CASES.items():
            with self.subTest(name):
                blocks = m.parse(md, "x")
                data, pages, _, _ = m.render(blocks, None, 9)
                m.verify(data, blocks, pages)

    def test_fix7_long_word_split_still_passes(self):
        # r2: was a 200-character token split across lines; now a long token is never split, so
        # use one that fits after the table font is reduced (the self-check must still pass)
        self.make("| A | B |\n|---|---|\n| %s | y |\n" % ("Q" * 110))


class TestChars(Base):
    def test_fix8_wide_chars_render(self):
        md = ("| A | B |\n|---|---|\n| non‑breaking | minus −5 |\n"
              "| 5 000 | 5 000 |\n| Zoë Ñandú | café “q” — |\n")
        pdf, _ = self.make(md)
        t = flat(pdf)
        self.assertIn("non‑breaking", t)
        self.assertIn("minus −5", t)
        self.assertEqual(t.count("5 000"), 2)
        self.assertIn("Zoë Ñandú", t)

    def test_fix8_font_is_system_ttf(self):
        pdf, _ = self.make("| A |\n|---|\n| x |\n")
        from pypdf import PdfReader
        names = set()
        for pg in PdfReader(pdf).pages:
            for f in pg["/Resources"]["/Font"].values():
                names.add(str(f.get_object()["/BaseFont"]))
        self.assertFalse([n for n in names if "Helvetica" in n], names)
        self.assertTrue([n for n in names if "Arial" in n], names)

    def test_fix8_missing_glyph_exit3_names_codepoint(self):
        for ch, cp in (("\U0001F600", "U+1F600"), ("\U0001F9D1", "U+1F9D1")):
            p = self.md("g.md", "| A | B |\n|---|---|\n| x | %s |\n" % ch)
            r = self.run_tool(p)
            self.assertEqual(r.returncode, 3, r.stderr)
            self.assertIn("g.md:3", r.stderr)
            self.assertIn(cp, r.stderr)

    def test_fix8_soft_hyphen_and_control_exit3(self):
        for ch, cp in (("­", "U+00AD"), ("\x07", "U+0007")):
            p = self.md("c.md", "| A | B |\n|---|---|\n| co%soperate | y |\n" % ch)
            r = self.run_tool(p)
            self.assertEqual(r.returncode, 3, r.stderr)
            self.assertIn("c.md:3", r.stderr)
            self.assertIn(cp, r.stderr)

    def test_fix8_zero_width_space_passes(self):
        self.make("| A | B |\n|---|---|\n| long​word | y |\n")


class TestAlign(Base):
    def test_fix9_alignment(self):
        md = ("| Name | Amt | Mid |\n| :--- | ---: | :---: |\n"
              "| a | 7 | x |\n| bb | 7000000 | yyyyyyyy |\n")
        pdf, _ = self.make(md)
        w = bbox(pdf)
        self.assertAlmostEqual(w["7"][1], w["7000000"][1], delta=0.6)   # right edges align
        self.assertGreater(w["7"][0], w["7000000"][0] + 10)
        cx = (w["x"][0] + w["x"][1]) / 2
        cy = (w["yyyyyyyy"][0] + w["yyyyyyyy"][1]) / 2
        self.assertAlmostEqual(cx, cy, delta=1.0)                       # centred
        self.assertAlmostEqual(w["a"][0], w["bb"][0], delta=0.6)        # left


class TestScripts(Base):
    def cell(self, text):
        p = self.md("s.md", "| A | B |\n|---|---|\n| x | %s |\n" % text)
        return self.run_tool(p)

    def test_shaping_scripts_refused_exit3(self):
        for text, script in (("\u0939\u093f\u0902\u0926\u0940", "DEVANAGARI"),
                             ("\u0e44\u0e17\u0e22", "THAI"), ("\u0b95", "TAMIL")):
            r = self.cell(text)
            self.assertEqual(r.returncode, 3, r.stderr)
            self.assertIn("s.md:3", r.stderr)
            self.assertIn("U+%04X" % ord(text[0]), r.stderr)
            self.assertIn(script, r.stderr)

    def test_rtl_refused_exit3(self):
        for text, script in (("\u05e9\u05dc\u05d5\u05dd", "HEBREW"), ("\u0645\u0631\u062d\u0628\u0627", "ARABIC"),
                             ("\u0710", "SYRIAC")):
            r = self.cell(text)
            self.assertEqual(r.returncode, 3, r.stderr)
            self.assertIn("right-to-left text not supported", r.stderr)
            self.assertIn(script, r.stderr)

    def test_other_scripts_still_render(self):
        pdf, _ = self.make("| A | B |\n|---|---|\n| \u03b1\u03b2\u03b3 | \u041f\u0440\u0438\u0432\u0435\u0442 |\n"
                           "| \u65e5\u672c | caf\u00e9 |\n")
        t = flat(pdf)
        for s in ("\u03b1\u03b2\u03b3", "\u041f\u0440\u0438\u0432\u0435\u0442", "\u65e5\u672c"):
            self.assertIn(s, t)

    def test_help_explains_markup_and_literal_default(self):
        out = self.run_tool("--help").stdout
        flat_help = " ".join(out.split())
        self.assertIn("removes ** and backticks when they form markers", flat_help)
        self.assertIn("literal mode is the default for exactly that reason", flat_help)


class TestPositionalOutput(Base):
    def test_positional_matches_dash_o(self):
        p = self.md("in.md", "| A | B |\n|---|---|\n| **x** | 2 |\n")
        a, b = os.path.join(self.d, "a.pdf"), os.path.join(self.d, "b.pdf")
        r1 = self.run_tool(p, a)
        r2 = self.run_tool(p, "-o", b)
        self.assertEqual((r1.returncode, r2.returncode), (0, 0), r1.stderr + r2.stderr)
        da, db = open(a, "rb").read(), open(b, "rb").read()
        if da != db:  # creation timestamp may differ: compare text and page count
            from pypdf import PdfReader
            ra, rb = PdfReader(a), PdfReader(b)
            self.assertEqual(len(ra.pages), len(rb.pages))
            self.assertEqual([x.extract_text() for x in ra.pages], [x.extract_text() for x in rb.pages])
        self.assertIn("**x**", flat(a))  # literal stays the default

    def test_positional_and_dash_o_exit2(self):
        p = self.md("in.md", "| A |\n|---|\n| x |\n")
        r = self.run_tool(p, os.path.join(self.d, "a.pdf"), "-o", os.path.join(self.d, "b.pdf"))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual([f for f in os.listdir(self.d) if f.endswith(".pdf")], [])

    def test_positional_not_pdf_exit2(self):
        p = self.md("in.md", "| A |\n|---|\n| x |\n")
        r = self.run_tool(p, os.path.join(self.d, "out.txt"))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.d, "out.txt")))
        self.assertEqual(self.run_tool(p, os.path.join(self.d, "OUT.PDF")).returncode, 0)


if __name__ == "__main__":
    unittest.main()
