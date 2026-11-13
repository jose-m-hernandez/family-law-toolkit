# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Section 4 of the compare spec: what counts as a difference, row by row (T2 to T18,
T20, T28's matching caps, T29 to T32, T34, T35). Each expectation is written from the spec."""

import random
import string
import time
import unittest

from family_law_toolkit.compare import differences
from tests.compare_support import (
    BILL, CURLY, CYRILLIC_A, FIXTURES, LINE_A, LINE_B, PA, PB, PC, RENT, T20_BASES, ZWSP,
    as_bytes, difference_lines, paragraphs, render, result_line, t35_pair, words_line,
)

OLD_NEW_1 = "old file paragraph 1, file line 1; new file paragraph 1, file line 1"


def lines_of(key):
    old, new = FIXTURES[key]
    return difference_lines(old, new)


def kinds_of(old, new):
    return [e.kind for e in differences.compare(as_bytes(old), as_bytes(new)).entries]


class DifferenceTests(unittest.TestCase):
    def test_t02_one_word_differs(self):
        self.assertEqual(lines_of("T2"), [
            "  1. Differs: " + OLD_NEW_1,
            "     old: Parent A picks up the children at 4:15 p.m. on Fridays.",
            "     new: Parent A picks up the children at 4:45 p.m. on Fridays.",
            '     - old file line 1, new file line 1: old "4:15", new "4:45", after "the children at"',
        ])

    def test_t03_paragraph_only_in_new(self):
        self.assertEqual(lines_of("T3a"), [
            "  1. Only in new: new file paragraph 1, file line 1; before old file paragraph 1",
            "     new: " + PA,
        ])
        self.assertEqual(lines_of("T3b"), [
            "  1. Only in new: new file paragraph 2, file line 3; after old file paragraph 1",
            "     new: " + PC,
        ])

    def test_t04_paragraph_only_in_old(self):
        self.assertEqual(lines_of("T4a"), [
            "  1. Only in old: old file paragraph 1, file line 1; before new file paragraph 1",
            "     old: " + PA,
        ])
        self.assertEqual(lines_of("T4b"), [
            "  1. Only in old: old file paragraph 2, file line 3; after new file paragraph 1",
            "     old: " + PC,
        ])

    def test_t05_two_paragraphs_against_three(self):
        self.assertEqual(lines_of("T5"), [
            "  1. Differs: old file paragraph 2, file line 3; new file paragraphs 2-3, file lines 3-5",
            "     old: " + BILL,
            "     new: Parent B pays",
            "     new: the bill.",
            '     - new file line 5: only in new (paragraph break), after "Parent B pays"',
        ])
        self.assertEqual(lines_of("T5b"), [
            "  1. Differs: old file paragraphs 1-2, file lines 1-3; new file paragraphs 1-3, file lines 1-5",
            "     old: alpha one",
            "     old: beta two",
            "     new: alpha uno",
            "     new: mid",
            "     new: beta dos",
            '     - old file line 1, new file lines 1-3: old "one", new "uno" (paragraph break) "mid", after "alpha"',
            '     - old file line 3, new file line 5: old "two", new "dos", after "beta"',
        ])

    def test_t06_paragraph_rewrapped(self):
        self.assertEqual(lines_of("T6"), [
            "  1. Spacing in the paragraph: old file paragraph 1, file line 1; "
            "new file paragraph 1, file lines 1-2",
        ])

    def test_t07_spacing_in_the_paragraph(self):
        for key in ("T7-tab", "T7-trailing", "T7-nbsp", "T7-u2000"):
            with self.subTest(key):
                self.assertEqual(lines_of(key), ["  1. Spacing in the paragraph: " + OLD_NEW_1])

    def test_t08_blank_line_between_equal_paragraphs(self):
        self.assertEqual(lines_of("T8"), [
            "  1. Spacing before the paragraph: old file paragraph 2, file line 3; "
            "new file paragraph 2, file line 4",
        ])

    def test_t08_first_paragraphs_compare_the_blank_lines_before_them(self):
        # 4.3: spacing before the paragraph is compared when both paragraphs are first in their files
        self.assertEqual(difference_lines(b"\nParent A pays.\n", b"Parent A pays.\n"), [
            "  1. Spacing before the paragraph: old file paragraph 1, file line 2; "
            "new file paragraph 1, file line 1",
        ])
        self.assertEqual(difference_lines(b"\n\na b\n", b"a b\n"), [
            "  1. Spacing before the paragraph: old file paragraph 1, file line 3; "
            "new file paragraph 1, file line 1",
        ])

    def test_t09_final_line_end_added(self):
        self.assertEqual(lines_of("T9"), ["  1. File: blank lines or line ends after the last paragraph differ"])

    def test_t10_line_end_kinds_and_order(self):
        self.assertEqual(lines_of("T10-crlf"), ["  1. File: line ends: old CRLF, new LF; first different at file line 1"])
        mixed = "mixed (CRLF 2, LF 1)"
        self.assertEqual(lines_of("T10-mixed-1"), [
            "  1. File: line ends: old %s, new %s; first different at file line 1" % (mixed, mixed)])
        self.assertEqual(lines_of("T10-mixed-2"), [
            "  1. File: line ends: old %s, new %s; first different at file line 2" % (mixed, mixed)])

    def test_t11_byte_order_mark(self):
        self.assertEqual(lines_of("T11-bom"), ["  1. File: byte-order mark in new only"])
        self.assertEqual(difference_lines(b"\xef\xbb\xbfParent A pays the rent.\n", b"Parent A pays the rent.\n"),
                         ["  1. File: byte-order mark in old only"])

    def test_t11_line_end_and_tail_combinations(self):
        self.assertEqual(lines_of("T11-none-lf"), [
            "  1. File: line ends: old none, new LF; first different at file line 1",
            "  2. File: blank lines or line ends after the last paragraph differ",
        ])
        self.assertEqual(lines_of("T11-order-edit"), [
            "  1. Differs: old file paragraph 2, file line 4; new file paragraph 2, file line 4",
            "     old: The exchange is at school.",
            "     new: The exchange is at the school.",
            '     - new file line 4: only in new "the", after "exchange is at"',
        ])
        self.assertEqual(lines_of("T11-new-kind"), [
            "  1. Only in new: new file paragraph 2, file line 3; after old file paragraph 1",
            "     new: " + BILL,
            "  2. File: line ends: old LF, new mixed (CRLF 1, LF 2); first different at file line 2",
        ])

    def test_t05_context_comes_from_the_new_file(self):
        # 5.3: the context comes from the new file, except for an only-in-old word
        self.assertEqual(difference_lines(b"one two three X\n", b"one 2 three Y\n"), [
            "  1. Differs: " + OLD_NEW_1,
            "     old: one two three X",
            "     new: one 2 three Y",
            '     - old file line 1, new file line 1: old "two", new "2", after "one"',
            '     - old file line 1, new file line 1: old "X", new "Y", after "one 2 three"',
        ])
        self.assertEqual(difference_lines(b"one 2 three X\n", b"one two three\n")[-1],
                         '     - old file line 1: only in old "X", after "one 2 three"')

    def test_t12_zero_width_space_in_a_word(self):
        self.assertEqual(lines_of("T12"), [
            "  1. Hidden or look-alike characters: " + OLD_NEW_1,
            '     - old "agree<U+200B>ment", new "agreement"',
        ])

    def test_t12_hidden_character_alone_between_spaces(self):
        # 4.3: it shows as both a Hidden or look-alike characters entry and a Spacing in the paragraph entry
        self.assertEqual(difference_lines(b"one two\n", ("one " + ZWSP + " two\n").encode("utf-8")), [
            "  1. Hidden or look-alike characters: " + OLD_NEW_1,
            '     - old (nothing), new "<U+200B>"',
            "  2. Spacing in the paragraph: " + OLD_NEW_1,
        ])

    def test_t13_composed_against_decomposed(self):
        self.assertEqual(lines_of("T13"), [
            "  1. Hidden or look-alike characters: " + OLD_NEW_1,
            '     - old "caf<U+00E9>.", new "cafe<U+0301>."',
        ])

    def test_t14_curly_quote(self):
        self.assertEqual(lines_of("T14")[1:], [
            "     old: Parent A's turn is on Friday.",
            "     new: Parent A" + CURLY + "s turn is on Friday.",
            '     - old file line 1, new file line 1: old "A\'s", new "A' + CURLY + 's", after "Parent"; '
            'as code points: old "A\'s", new "A<U+2019>s"',
        ])
        self.assertEqual(kinds_of(*FIXTURES["T14"]), ["differs"])

    def test_t15_case_change(self):
        self.assertEqual(lines_of("T15")[-1],
                         '     - old file line 1, new file line 1: old "Friday.", new "friday.", after "A pays on"')

    def test_t16_markdown_markup(self):
        self.assertEqual(lines_of("T16")[-1],
                         '     - old file line 1, new file line 1: old "**Friday**", new "Friday", '
                         'after "the children on"')

    def test_t17_cyrillic_letter(self):
        self.assertEqual(kinds_of(*FIXTURES["T17"]), ["differs"])
        self.assertEqual(lines_of("T17")[-1],
                         '     - old file line 1, new file line 1: old "Parent", new "P' + CYRILLIC_A + 'rent", '
                         'at the start of a paragraph; as code points: old "Parent", new "P<U+0430>rent"')

    def test_t18_paragraphs_rotated(self):
        self.assertEqual(lines_of("T18"), [
            "  1. Only in old: old file paragraph 1, file line 1; before new file paragraph 1",
            "     old: " + PA,
            "  2. Only in new: new file paragraph 3, file line 5; after old file paragraph 3",
            "     new: " + PA,
        ])

    def test_t20_no_hidden_byte_difference(self):
        rng = random.Random(20261111)
        pool = list(string.ascii_letters)
        pool += [chr(c) for c in range(0x3100) if chr(c).isspace()]
        pool += ["\r", chr(0xFEFF), chr(0x200B), chr(0xAD), chr(0x2060), chr(0x200E)]
        accepted = refused = 0
        for base in T20_BASES:
            old = base.encode("utf-8")
            differences.check(old)
            for _ in range(500):
                text = base
                position = rng.randrange(len(text) + 1)
                operation = rng.choice(("insert", "delete", "replace"))
                character = rng.choice(pool)
                if operation == "insert" or not text:
                    text = text[:position] + character + text[position:]
                elif operation == "delete":
                    position = min(position, len(text) - 1)
                    text = text[:position] + text[position + 1:]
                else:
                    position = min(position, len(text) - 1)
                    text = text[:position] + character + text[position + 1:]
                edited = text.encode("utf-8")
                if edited == old:
                    continue
                try:
                    differences.check(edited)
                except differences.Refused:
                    refused += 1
                    continue
                accepted += 1
                result = differences.compare(old, edited)
                self.assertFalse(result.identical)
                self.assertGreaterEqual(len(result.entries), 1, (base, edited))
        self.assertGreater(refused, 0)  # positive control: the generator does make refused files
        self.assertGreater(accepted, 1000)

    def test_t28_matching_caps(self):
        def shaped(first, last, count):
            return first + " " + " ".join(["a"] * (count - 2)) + " " + last + "\n"

        def timed(old, new):
            started = time.monotonic()
            result = differences.compare(as_bytes(old), as_bytes(new))
            self.assertLess(time.monotonic() - started, 10)
            return result

        def many(prefix, count):
            return paragraphs(*["%s %d" % (prefix, n) for n in range(count)])

        # paragraph matching: 500 x 500 runs, 501 x 500 cannot
        timed(many("old", 500), many("new", 500))
        started = time.monotonic()
        with self.assertRaises(differences.TooManyParagraphs):
            differences.compare(many("old", 501).encode(), many("new", 500).encode())
        self.assertLess(time.monotonic() - started, 10)
        # one word matching: 500 x 500 runs, 501 x 501 loses its word differences
        shown = timed(shaped("p", "q", 500), shaped("r", "s", 500)).entries[0]
        self.assertEqual(len(shown.diffs), 2)
        shown = timed(shaped("p", "q", 501), shaped("r", "s", 501)).entries[0]
        self.assertIsNone(shown.diffs)
        # one piece matching (hidden characters): the same two sizes
        def hidden(count, marked):
            mark = ZWSP if marked else ""
            return "a" + mark + " " + " ".join(["b"] * (count - 2)) + " c" + mark + "\n"
        entry = timed(hidden(500, True), hidden(500, False)).entries[0]
        self.assertEqual((entry.kind, len(entry.runs)), ("hidden", 2))
        entry = timed(hidden(501, True), hidden(501, False)).entries[0]
        self.assertEqual((entry.kind, entry.runs), ("hidden", None))
        # the shared total: two 500 x 500 matchings run, a third of 2 x 3 does not
        old = paragraphs(words_line(500, "a"), PB, words_line(500, "c"), PB, "one two")
        new = paragraphs(words_line(500, "b"), PB, words_line(500, "d"), PB, "x y z")
        entries = timed(old, new).entries
        self.assertEqual([e.diffs is None for e in entries], [False, False, True])

    def _single_token(self, key, expected_line, header=OLD_NEW_1):
        old, new = FIXTURES[key]
        self.assertGreaterEqual(len(old.split()), 300)
        self.assertEqual(kinds_of(old, new), ["differs"])
        lines = lines_of(key)
        self.assertEqual(lines[0], "  1. Differs: " + header)
        self.assertEqual([l for l in lines if l.startswith("     - ")], ["     - " + expected_line])

    def test_t29_figure_in_long_paragraph(self):
        for key in ("T29", "T29-extras"):
            with self.subTest(key):
                self._single_token(key, 'old file line 1, new file line 1: old "$1,200.00", new "$1,250.00", '
                                        'after "the sum of"')

    def test_t30_date_in_long_paragraph(self):
        for key in ("T30", "T30-extras"):
            with self.subTest(key):
                self._single_token(key, 'old file line 1, new file line 1: old "3", new "8", after "due on March"')

    def test_t31_negation_in_long_paragraph(self):
        for key in ("T31", "T31-extras"):
            with self.subTest(key):
                self._single_token(key, 'new file line 1: only in new "not", after "Parent B shall"')

    def test_t32_checkbox_at_paragraph_start(self):
        for key in ("T32", "T32-extras"):
            with self.subTest(key):
                self._single_token(key, 'old file line 1, new file line 1: old "[X]", new "[ ]", '
                                        'at the start of a paragraph')

    def test_t34_matching_limit_lone_figure(self):
        old, new = FIXTURES["T34"]
        lines = difference_lines(old, new)
        self.assertEqual(kinds_of(old, new), ["differs"] * 3)
        self.assertEqual(result_line(old, new), "Result: the files differ. Differs 3, only in old 0, only in new 0, "
                         "spacing 0, hidden or look-alike characters 0, file 0.")
        heads = [l for l in lines if l.startswith("  ") and not l.startswith("     ")]
        self.assertEqual(heads[2], "  3. Differs: old file paragraph 5, file line 9; new file paragraph 5, file line 9")
        third = lines[lines.index(heads[2]):]
        self.assertEqual(third, [
            heads[2],
            "     old: Parent A will pay $1,200.00 each month.",
            "     new: Parent A will pay $1,250.00 each month.",
            "     " + LINE_A,
        ])
        self.assertFalse([l for l in lines if "no difference" in l.lower()])
        # the first two ran: each lists its word differences
        self.assertEqual(len([l for l in lines if l.startswith("     - ")]), 2)

    def test_t35_matching_limit_hidden_characters(self):
        old, new = FIXTURES["T35"]
        self.assertEqual(kinds_of(old, new), ["hidden"])
        lines = difference_lines(old, new)
        self.assertEqual(lines, [
            "  1. Hidden or look-alike characters: old file paragraph 1, file line 1; "
            "new file paragraph 1, file line 1",
            "     " + LINE_B,
        ])
        text = render(old, new)
        self.assertEqual(result_line(old, new), "Result: the files differ. Differs 0, only in old 0, only in new 0, "
                         "spacing 0, hidden or look-alike characters 1, file 0.")
        self.assertNotIn("words, figures and dates", text)
        self.assertNotIn("no difference", text.lower())
        # one piece fewer on each side: 500 x 500 = 250,000 runs, and lists its two runs
        old, new = t35_pair(500)
        lines = difference_lines(old, new)
        self.assertEqual(lines[1:], ['     - old "a", new "a<U+200B>"', '     - old "z", new "z<U+200B>"'])
        self.assertNotIn("Detail not shown", "\n".join(lines))


if __name__ == "__main__":
    unittest.main()
