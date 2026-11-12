# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Sections 5 and 6 of the compare spec, at report level (T19's report parts, T24, T25,
T27, T33). The fixed lines are read from the spec itself, so a drift from it fails."""

import errno
import hashlib
import os
import re
import textwrap
import unittest
from unittest import mock

from family_law_toolkit.compare import differences, report
from tests.compare_support import (
    FIXTURES, GOLDEN_NEW, LINE_A, LINE_B, GOLDEN_OLD, GOLDEN_PATHS, PA, PB, ROOT, T20_BASES, Workdir,
    FakeStream, as_bytes, difference_lines, page_free_lines, paragraphs, raw_difference_lines, render,
    result_line, run_main, spec_help,
    spec_detail_lines, spec_identity_line, spec_listed_phrases, spec_notes,
)

EDUCATIONAL = "Educational; not legal advice; not certified for court filing; consult counsel."
Q_C7_SENTENCE = "The report is not a certified comparison and is not a court record."


def WRAP(line):
    return textwrap.wrap(line, width=78, subsequent_indent=" " * 7,
                         break_long_words=False, break_on_hyphens=False)


def wrapped_notes():
    return [
        line for note in spec_notes()
        for line in textwrap.wrap("  " + note, width=78, subsequent_indent="  ",
                                  break_long_words=False, break_on_hyphens=False)
    ]


def phrase_hits(lines):
    """(line, phrase) for each section 6 word or phrase found as a whole word, in any case."""
    hits = []
    for phrase in spec_listed_phrases():
        pattern = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", re.I)
        hits += [(line, phrase) for line in lines if pattern.search(line)]
    return hits


def generated_lines(text):
    """The lines the tool generates about the two files: not the identity lines, the
    Educational line or the Notes block."""
    lines = page_free_lines(text)
    return [line for line in lines[:lines.index("Notes")] if line != EDUCATIONAL]


def fixed_line_problems(text):
    """What differs from the spec in the report's fixed lines (identity line on every page,
    the Educational line, the Notes block)."""
    problems = []
    for page in text.split("\f"):
        if page.split("\n")[:2] != [spec_identity_line(), ""]:
            problems.append("identity line")
    lines = page_free_lines(text)
    if lines[1] != EDUCATIONAL:
        problems.append("Educational line")
    if lines[lines.index("Notes") + 1:] != wrapped_notes():
        problems.append("Notes block")
    return problems


class ReportTests(unittest.TestCase):
    def test_t19_escaping_in_report(self):
        raw = {"T19-esc": ["\x1b", chr(0x202E)], "T19-lt": [chr(0x200B)], "T19-ff": ["\x0c", chr(0x2028)]}
        expected = {
            "T19-esc": [
                "  1. Differs: old file paragraph 1, file line 1; new file paragraph 1, file line 1",
                "     old: Parent A said hello.",
                "     new: Parent A said hel<U+001B>lo<U+202E>.",
                '     - old file line 1, new file line 1: old "hello.", new "hel<U+001B>lo<U+202E>.", '
                'after "Parent A said"; as code points: old "hello.", new "hel<U+001B>lo<U+202E>."',
            ],
            "T19-quote": [
                "  1. Differs: old file paragraph 1, file line 1; new file paragraph 1, file line 1",
                '     old: Parent A said "hello".',
                '     new: Parent A said "goodbye".',
                '     - old file line 1, new file line 1: old "<U+0022>hello<U+0022>.", '
                'new "<U+0022>goodbye<U+0022>.", after "Parent A said"',
            ],
            "T19-lt": [
                "  1. Differs: old file paragraph 1, file line 1; new file paragraph 1, file line 1",
                "     old: Parent A has <U+003C>U+200B> today.",
                "     new: Parent A has today.",
                '     - old file line 1: only in old "<U+003C>U+200B>", after "Parent A has"',
            ],
            "T19-ff": [
                "  1. Spacing in the paragraph: old file paragraph 1, file line 1; "
                "new file paragraph 1, file line 1",
            ],
        }
        for key, lines in expected.items():
            old, new = FIXTURES[key]
            with self.subTest(key):
                self.assertEqual(difference_lines(old, new), lines)
                text = render(old, new)
                for character in raw.get(key, []):
                    self.assertNotIn(character, text)
                # the exact number of lines: identity line and blank, the 14 lines down to
                # "Differences", the entry's lines as wrapped, a blank line, "Notes", the Notes
                entry = sum(len(WRAP(line)) if line.startswith("     ") else 1 for line in lines)
                self.assertEqual(len(text.split("\n")) - 1, 2 + 14 + entry + 2 + len(wrapped_notes()))
        text = render(*FIXTURES["T19-ff"])
        self.assertIn("    %d bytes; 1 line; 1 paragraph;" % len(FIXTURES["T19-ff"][0].encode()), text)

    def test_t24_never_say(self):
        phrases = spec_listed_phrases()
        self.assertIn("significant", phrases)
        # the two detail lines: byte for byte against the spec's 4.4, and not the old line
        self.assertEqual(spec_detail_lines(), {"A": LINE_A, "B": LINE_B})
        self.assertNotEqual(LINE_A, LINE_B)
        for line, kind in ((LINE_A, "T34"), (LINE_B, "T35")):
            text = render(*FIXTURES[kind])
            self.assertEqual(len(WRAP("     " + line)), 3)
            self.assertIn("\n".join(WRAP("     " + line)) + "\n", text)
            self.assertNotIn("this paragraph; words", text)
        # the fixtures hold none of the words, so a hit can only be the tool's own text
        texts = [as_bytes(t).decode("utf-8") for pair in FIXTURES.values() for t in pair]
        texts += list(T20_BASES) + [GOLDEN_OLD, GOLDEN_NEW]
        self.assertEqual(phrase_hits(texts), [])
        self.assertEqual(phrase_hits(["old.txt", "new.txt"]), [])
        reports = [render(old, new) for old, new in FIXTURES.values()]
        reports += [render(GOLDEN_OLD, GOLDEN_NEW), render(PA + "\n", PA + "\n")]
        for text in reports:
            self.assertEqual(phrase_hits(generated_lines(text)), [])
            self.assertEqual(fixed_line_problems(text), [])
        # section 7 messages, with each path taken out
        work = Workdir()
        self.addCleanup(work.cleanup)
        good = work.write("good.txt", PA + "\n")
        empty = work.write("empty.txt", b"")
        nul = work.write("nul.txt", b"a\x00b")
        bad = work.write("bad.txt", b"\xff")
        big = work.write("big.txt", b"a" * 200001)
        pdf = work.write("x.pdf", PA)
        many_old = work.write("many_old.txt", "\n\n".join("old %d" % n for n in range(501)))
        many_new = work.write("many_new.txt", "\n\n".join("new %d" % n for n in range(500)))
        cases = [
            [], ["--old", good], ["--old", good, "--new", good], ["--old", "-", "--new", good],
            ["--old", good, "--old", good, "--new", good], ["--old", good, "--new", good, "--x"],
            ["--old", work.path, "--new", good], ["--old", "/dev/null", "--new", good],
            ["--old", good, "--new", work.path + "/none.txt"], ["--old", good, "--new", big],
            ["--old", good, "--new", pdf], ["--old", good, "--new", nul], ["--old", bad, "--new", good],
            ["--old", good, "--new", empty], ["--old", many_old, "--new", many_new],
        ]
        lines = []
        for argv in cases:
            code, out, err = run_main(argv)
            self.assertEqual((code, out), (2, b""), argv)
            line = err.decode("utf-8").rstrip("\n")
            self.assertEqual(err.count(b"\n"), 1, argv)
            lines.append(line.replace(work.path, "DIR"))
        with mock.patch.object(differences, "compare", side_effect=RuntimeError("boom")):
            lines.append(run_main(["--old", good, "--new", many_new])[2].decode().rstrip("\n"))
        # the three messages the cases above do not reach: a failing write, and the two reasons that
        # the file system can give for a file that cannot be read
        other = work.write("other.txt", PB + "\n")
        lines.append(run_main(["--old", good, "--new", other], stdout=FakeStream(fail_after_bytes=0))[2]
                     .decode().rstrip("\n"))
        for number in (errno.EPERM, errno.EIO):
            real_stat = os.stat

            def stat(path, *args, **kwargs):
                if path == good:
                    raise OSError(number, "refused")
                return real_stat(path, *args, **kwargs)

            with mock.patch.object(os, "stat", side_effect=stat):
                code, out, err = run_main(["--old", good, "--new", other])
            self.assertEqual((code, out, err.count(b"\n")), (2, b"", 1))
            lines.append(err.decode().rstrip("\n"))
        self.assertEqual(phrase_hits([l.replace("python3 -m family_law_toolkit.compare: error: ", "") for l in lines]), [])
        # positive control: the last three lines are the three messages added above
        self.assertEqual([l.split(": ")[-1] for l in lines[-3:]],
                         ["cannot write output", "permission denied", "it could not be read"])
        # the help: every line but the help sentences and the Educational line
        help_lines = spec_help().split("\n")
        exempt = {EDUCATIONAL, Q_C7_SENTENCE}
        self.assertEqual({line for line, _ in phrase_hits(help_lines)} - exempt, set())
        self.assertEqual(run_main(["--help"])[1], (spec_help() + "\n").encode("utf-8"))
        # positive controls: a listed word in generated text, and a changed fixed line
        text = render(*FIXTURES["T2"])
        planted = text.replace("Result: the files differ.", "Result: the files differ in a significant way.")
        self.assertNotEqual(planted, text)
        self.assertEqual(phrase_hits(generated_lines(planted))[0][1], "significant")
        for before, after in (("Moves are not", "Move are not"), ("Educational;", "Educational,")):
            changed = text.replace(before, after)
            self.assertNotEqual(changed, text)
            self.assertNotEqual(fixed_line_problems(changed), [])
        long_text = render(GOLDEN_OLD, GOLDEN_NEW)
        self.assertEqual(len(long_text.split("\f")), 2)
        changed = long_text.replace("\f" + spec_identity_line(), "\f" + spec_identity_line() + "!")
        self.assertIn("identity line", fixed_line_problems(changed))

    def test_t27_result_line_counts(self):
        head = "Result: the files differ. "
        # 5.2: `spacing` counts both spacing labels, `file` counts every File entry
        t8 = result_line(*FIXTURES["T8"])
        self.assertEqual(t8, head + "Differs 0, only in old 0, only in new 0, spacing 1, "
                         "hidden or look-alike characters 0, file 0.")
        both = (paragraphs("a b", "c d"), "a\tb\n\n\n\nc d\n")
        self.assertEqual(raw_difference_lines(*both), [
            "  1. Spacing in the paragraph: old file paragraph 1, file line 1; new file paragraph 1, file line 1",
            "  2. Spacing before the paragraph: old file paragraph 2, file line 3; new file paragraph 2, file line 5",
        ])
        self.assertEqual(result_line(*both), head + "Differs 0, only in old 0, only in new 0, spacing 2, "
                         "hidden or look-alike characters 0, file 0.")
        self.assertEqual(result_line(b"abc", b"abc\n"), head + "Differs 0, only in old 0, only in new 0, "
                         "spacing 0, hidden or look-alike characters 0, file 2.")

    def test_t19_a_control_character_alone_adds_the_code_points(self):
        # 5.3: a character outside printable ASCII (U+0020 to U+007E) adds `; as code points:`
        start = "     - old file line 1, new file line 1: "
        self.assertEqual(difference_lines(b"one two\n", b"one two\x7f\n")[-1],
                         start + 'old "two", new "two<U+007F>", after "one"; as code points: '
                         'old "two", new "two<U+007F>"')
        self.assertEqual(difference_lines(b"one two\n", b"one two\x1b\n")[-1],
                         start + 'old "two", new "two<U+001B>", after "one"; as code points: '
                         'old "two", new "two<U+001B>"')
        self.assertEqual(difference_lines(b"x\n", b"x \x1b\n")[-1],
                         '     - new file line 1: only in new "<U+001B>", after "x"; as code points: '
                         'only in new "<U+001B>"')
        # and a piece of printable ASCII alone adds nothing
        self.assertNotIn("as code points", difference_lines(b"one two\n", b"one 2\n")[-1])

    def test_t19_long_tokens_are_not_split_across_lines(self):
        # 5.2: break_long_words=False, break_on_hyphens=False; a longer word runs past 78
        plain = ("x" * 110, "y" * 110)
        hyphenated = ("p" * 40 + "-" + "q" * 40 + "-" + "r" * 20, "p" * 40 + "-" + "s" * 40 + "-" + "r" * 20)
        for old, new in (plain, hyphenated):
            with self.subTest(old=old[:5] + "..."):
                lines = raw_difference_lines("a " + old + "\n", "a " + new + "\n")
                self.assertEqual(lines, [
                    "  1. Differs: old file paragraph 1, file line 1; new file paragraph 1, file line 1",
                    "     old: a",
                    "       " + old,
                    "     new: a",
                    "       " + new,
                    "     - old file line 1, new file line 1: old",
                    '       "' + old + '",',
                    "       new",
                    '       "' + new + '",',
                    '       after "a"',
                ])

    def test_t25_determinism(self):
        old, new = FIXTURES["T2"]
        self.assertEqual(render(old, new), render(old, new))
        lines = render(old, new, "./drafts/../old.txt", "new.txt").split("\n")
        self.assertIn("  Old (--old): ./drafts/../old.txt", lines)
        self.assertIn("  New (--new): new.txt", lines)

    def test_t27_golden_report(self):
        expected = (ROOT / "tests" / "golden" / "compare_report.txt").read_bytes()
        actual = render(GOLDEN_OLD, GOLDEN_NEW, *GOLDEN_PATHS).encode("utf-8")
        self.assertEqual(actual, expected)
        pages = expected.decode("utf-8").split("\f")
        self.assertEqual([len(page.split("\n")) for page in pages[:-1]], [60])
        self.assertTrue(all(page.startswith(spec_identity_line() + "\n\n") for page in pages))
        self.assertTrue(expected.endswith(b"\n") and not expected.endswith(b"\n\n"))
        self.assertIn(b"v0.1.0", expected)

    def test_t33_header_paths_sizes_hashes(self):
        old = b"\xef\xbb\xbf" + (PA + "\n").encode()
        new = (PB + "\n").encode()
        text = render(old, new, "./a.txt", "b/c.txt")
        lines = text.split("\n")
        start = lines.index("Files")
        self.assertEqual(lines[start + 1:start + 7], [
            "  Old (--old): ./a.txt",
            "    %s bytes; 1 line; 1 paragraph; byte-order mark: yes; line ends: LF" % len(old),
            "    sha256: " + hashlib.sha256(old).hexdigest(),
            "  New (--new): b/c.txt",
            "    %s bytes; 1 line; 1 paragraph; byte-order mark: no; line ends: LF" % len(new),
            "    sha256: " + hashlib.sha256(new).hexdigest(),
        ])
        edited = new.replace(b"school", b"schoon")
        again = render(old, edited, "./a.txt", "b/c.txt").split("\n")
        changed = [i for i in range(start, start + 7) if lines[i] != again[i]]
        self.assertEqual(changed, [start + 6])
        self.assertEqual(again[start + 6], "    sha256: " + hashlib.sha256(edited).hexdigest())
        single = render(b"a", b"b").split("\n")
        self.assertEqual(single[single.index("Files") + 2],
                         "    1 byte; 1 line; 1 paragraph; byte-order mark: no; line ends: none")


if __name__ == "__main__":
    unittest.main()
