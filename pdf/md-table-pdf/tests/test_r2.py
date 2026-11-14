# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Round 2 tests: keep-with-next headings (first section on page 1) and unbreakable tokens.
Synthetic fixtures only (make_fixtures.py)."""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_md_table_pdf import Base, PDFTOTEXT, fx  # noqa: E402
from pypdf import PdfReader  # noqa: E402


def layout_lines(pdf, n):
    out = subprocess.run([PDFTOTEXT, "-layout", "-f", str(n), "-l", str(n), pdf, "-"],
                         check=True, capture_output=True, text=True).stdout
    return [ln for ln in out.splitlines() if ln.strip()]


def body_lines(pdf, n):
    """Page n's lines without the 'page x of y' footer."""
    return [ln for ln in layout_lines(pdf, n) if not ln.strip().startswith("page ")]


def npages(pdf):
    return len(PdfReader(pdf).pages)


class TestKeepWithNext(Base):
    def test_r2_first_section_starts_on_page_1(self):
        # H1 + subtitle + 3 H2 sections with 15, 5 and 4 rows = 24 rows over 3 tables.
        # Content height (reportlab, at the real column widths, 9 pt): title block 49.1 pt, then
        # per section heading 24.6 + table + spacer 9: tables are 444.75, 159.75 and 131.25 pt
        # (header row 17.25, a two-line row 28.5), 901.8 pt in all (an upper bound: it counts
        # the paragraph spacing the frame collapses). One page holds 506.4 pt (landscape Letter,
        # 0.6 in top, 0.7 in bottom margin, 6 pt frame padding each side), two hold 1012.8:
        # 506.4 < 901.8 <= 1012.8, and a table may split across pages row by row, so the minimum
        # is exactly 2 pages. Page 1 has 506.4 - 49.1 = 457.3 pt left after the title block;
        # section 1 whole needs 469.4 (does not fit), but its heading + header row + first row
        # need 70.4 (fits). The old tool kept heading + whole table together, moved section 1 to
        # page 2 and printed 3 pages.
        pdf, r = self.make(fx.sections((15, 5, 4)))
        self.assertIn("3 tables, 24 body rows, 2 pages", r.stdout)
        self.assertEqual(npages(pdf), 2)
        p1 = body_lines(pdf, 1)
        self.assertIn("Matter Summary", p1[0])
        self.assertTrue(any("Section 1" in ln for ln in p1), p1)
        self.assertTrue(any("3/01/2031" in ln for ln in p1), p1)  # first row of section 1
        self.assertFalse(any("Section 3" in ln for ln in p1))
        self.assertTrue(any("3/15/2031" in ln for ln in body_lines(pdf, 2)))  # table 1 continues

    def test_r2_heading_without_room_for_a_row_moves_with_its_table(self):
        # Table 1 (23 rows) leaves room on page 1 for the "Second" heading but not for its
        # header row plus one row: heading and table both go to page 2, none stays behind.
        pdf, _ = self.make(fx.two_sections(23, 45))
        p1, p2 = body_lines(pdf, 1), body_lines(pdf, 2)
        self.assertIn("a22", p1[-1])
        self.assertFalse(any("Second" in ln for ln in p1), p1)
        self.assertIn("Second", p2[0])
        self.assertIn("c0", p2[2])  # heading, header row, first body row

    def test_r2_heading_follows_a_table_that_spills_onto_page_2(self):
        # Table 1 ends high on page 2; section 2 starts right below it, not on a fresh page.
        pdf, _ = self.make(fx.two_sections(26, 45))
        self.assertEqual(npages(pdf), 3)
        p2 = body_lines(pdf, 2)
        self.assertTrue(any("Second" in ln for ln in p2), p2)
        self.assertFalse(any("Second" in ln for ln in body_lines(pdf, 3)))

    def test_r2_no_page_ends_or_starts_with_a_lone_heading(self):
        for n1 in range(18, 30):
            with self.subTest(n1=n1):
                pdf, _ = self.make(fx.two_sections(n1, 45), "d%d.md" % n1)
                for k in range(1, npages(pdf) + 1):
                    last = body_lines(pdf, k)[-1]
                    self.assertNotRegex(last.strip(), r"^(Doc|First|Second)$", (k, last))


class TestUnbreakableTokens(Base):
    def test_r2_dates_never_wrap_mid_token(self):
        pdf, _ = self.make(fx.narrow_dates())
        lines = [ln for k in range(1, npages(pdf) + 1) for ln in body_lines(pdf, k)]
        for tok in fx.DATE_TOKENS:
            with self.subTest(tok=tok):
                self.assertEqual(sum(ln.count(tok) for ln in lines), 1, tok)

    def test_r2_long_token_shrinks_the_table_font_and_stays_whole(self):
        tok = "Q" * 110
        p = self.md("long.md", "| A | B |\n|---|---|\n| %s | y |\n| z | w |\n" % tok)
        r = self.run_tool(p)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("note: table 1 set at", r.stderr)
        pdf = os.path.join(self.d, "long.pdf")
        lines = body_lines(pdf, 1)
        self.assertEqual(sum(ln.count(tok) for ln in lines), 1)

    def test_r2_text_with_spaces_still_wraps_at_spaces(self):
        # r2 must not stop ordinary wrapping: a long sentence in a cell takes several lines
        pdf, _ = self.make(fx.long_cell())
        self.assertGreater(len(body_lines(pdf, 1)), 6)

    def test_r2_unfittable_token_exits_nonzero_naming_table_and_length(self):
        md = ("| A | B |\n|---|---|\n| 1 | 2 |\n\n"
              "| C | D |\n|---|---|\n| %s | y |\n" % ("X" * 300))
        p = self.md("big.md", md)
        r = self.run_tool(p)
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("big.md:7", r.stderr)
        self.assertIn("table 2", r.stderr)
        self.assertIn("300 characters", r.stderr)
        self.assertIn("6 pt", r.stderr)  # the floor
        self.assertFalse(os.path.exists(os.path.join(self.d, "big.pdf")))
        self.assertEqual(r.stdout, "")

    def test_r2_floor_never_below_requested_size(self):
        # The floor is 6 pt, or the requested size when that is smaller. 180 X need about 5.9 pt
        # of width per point of size: too wide at the 6 pt floor (default size exits 3) but it
        # fits when the user asked for 5 pt, and 250 X fits at neither (exit 3 naming 5 pt).
        p = self.md("f.md", "| A | B |\n|---|---|\n| %s | y |\n" % ("X" * 180))
        r = self.run_tool(p)
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("6 pt", r.stderr)
        r = self.run_tool(p, "--font-size", "5")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")
        p = self.md("g.md", "| A | B |\n|---|---|\n| %s | y |\n" % ("X" * 250))
        r = self.run_tool(p, "--font-size", "5")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("5 pt", r.stderr)


if __name__ == "__main__":
    unittest.main()
