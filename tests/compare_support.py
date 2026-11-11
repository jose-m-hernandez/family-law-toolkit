# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Shared invented fixtures and helpers for the compare tests (not a test module).

Every text is invented: Parent A, Parent B, invented sums and dates. FIXTURES maps a
T-number key to (old, new), each text or bytes; every pair differs, so the command
exits 1 on each.
"""

import io
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

from family_law_toolkit import __version__
from family_law_toolkit.compare import __main__ as cli_main
from family_law_toolkit.compare import differences, report

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "docs" / "specs" / "compare-drafts.md"
PREFIX = "python3 -m family_law_toolkit.compare: error: "
USAGE_END = ". Run with --help to see what each flag means."

# Characters that are invisible or look alike, built here so no source line holds one raw.
ZWSP = chr(0x200B)
NBSP = chr(0xA0)
EN_SPACE = chr(0x2002)
EN_QUAD = chr(0x2000)
E_ACUTE = chr(0xE9)
ACUTE = chr(0x301)
CURLY = chr(0x2019)
CYRILLIC_A = chr(0x430)
RLO = chr(0x202E)
LINE_SEP = chr(0x2028)

PA = "Parent A picks up the children."
PB = "Parent B drops them off at the school."
PC = "The exchange is at the school gate."
RENT = "Parent A pays the rent."
BILL = "Parent B pays the bill."
FILLER = "Parent A and Parent B share the care of the children. "


def as_bytes(value):
    return value.encode("utf-8") if isinstance(value, str) else value


def paragraphs(*texts):
    return "\n\n".join(texts) + "\n"


def long_pair(old_sentence, new_sentence, at_start=False):
    """One long paragraph (over 400 words) holding one differing sentence."""
    before, after = ("", FILLER * 30) if at_start else (FILLER * 20, FILLER * 20)
    return (before + old_sentence + " " + after).rstrip() + "\n", (before + new_sentence + " " + after).rstrip() + "\n"


def _extras(new):
    """A tab for a space and a U+200B inside a word, both in the last filler sentence."""
    head, _, tail = new.rpartition("share the care of the children.")
    return head + "share the\tcare of the chil" + ZWSP + "dren." + tail


def token_pair(old_sentence, new_sentence, at_start=False, extras=False):
    old, new = long_pair(old_sentence, new_sentence, at_start)
    return old, (_extras(new) if extras else new)


def words_line(count, word):
    return " ".join([word] * count)


T34_SECOND = "Parent A and Parent B share the care of the children."


def t34_pair():
    old = paragraphs(words_line(500, "a"), T34_SECOND, words_line(500, "c"), T34_SECOND,
                     "Parent A will pay $1,200.00 each month.")
    new = paragraphs(words_line(500, "b"), T34_SECOND, words_line(500, "d"), T34_SECOND,
                     "Parent A will pay $1,250.00 each month.")
    return old, new


T29 = ("Parent A will pay the sum of $1,200.00 each month.", "Parent A will pay the sum of $1,250.00 each month.")
T30 = ("The payment is due on March 3 of each year.", "The payment is due on March 8 of each year.")
T31 = ("Parent B shall pay the school fees.", "Parent B shall not pay the school fees.")
T32 = ("[X] Parent A will attend the meeting.", "[ ] Parent A will attend the meeting.")

# The T27 golden pair: shaped like the spec's 5.2 example, with a Differs entry that reaches
# the matching limit (501 x 500 words), a Hidden or look-alike characters entry over two
# lines, a one-line Spacing entry and an Only in new entry.
GOLDEN_PATHS = ("drafts/declaration-v1.txt", "drafts/declaration-v2.txt")
GOLDEN_OLD = "\n".join([
    "Parent A picks up the children at the school on Fridays.", "",
    words_line(501, "a"), "",
    "Parent B keeps the agreement", "for the children.", "",
    "Parent A and Parent B meet at the school gate.",
]) + "\n"
GOLDEN_NEW = "\n".join([
    "Parent A picks up the children at the school on Fridays.", "",
    words_line(500, "b"), "",
    "Parent B keeps the agree" + ZWSP + "ment", "for the children.", "",
    "Parent A and Parent B meet at the school gate. ", "",
    "The exchange is at the school.",
]) + "\n"

FIXTURES = {
    "T2": ("Parent A picks up the children at 6:00 p.m. on Fridays.\n",
           "Parent A picks up the children at 6:30 p.m. on Fridays.\n"),
    "T3a": (paragraphs(PB), paragraphs(PA, PB)),
    "T3b": (paragraphs(PA, PB), paragraphs(PA, PC, PB)),
    "T4a": (paragraphs(PA, PB), paragraphs(PB)),
    "T4b": (paragraphs(PA, PC, PB), paragraphs(PA, PB)),
    "T5": (paragraphs(RENT, BILL), paragraphs(RENT, "Parent B pays", "the bill.")),
    "T5b": ("alpha one\n\nbeta two\n", "alpha uno\n\nmid\n\nbeta dos\n"),
    "T6": ("Parent A picks up the children at the school on Fridays.\n",
           "Parent A picks up the children\nat the school on Fridays.\n"),
    "T7-tab": ("Parent A pays on Fridays.\n", "Parent A\tpays on Fridays.\n"),
    "T7-trailing": ("Parent A pays on Fridays.\n", "Parent A pays on Fridays. \n"),
    "T7-nbsp": ("Parent A pays on Fridays.\n", "Parent A pays" + NBSP + "on Fridays.\n"),
    "T7-u2000": ("Parent A pays" + EN_SPACE + "on Fridays.\n", "Parent A pays" + EN_QUAD + "on Fridays.\n"),
    "T8": (paragraphs(RENT, BILL), RENT + "\n\n\n" + BILL + "\n"),
    "T9": ("Parent A pays the rent.\nParent B pays the bill.\nThe exchange is at school.",
           "Parent A pays the rent.\nParent B pays the bill.\nThe exchange is at school.\n"),
    "T10-crlf": (b"Parent A pays the rent.\r\nParent B pays the bill.\r\n",
                 b"Parent A pays the rent.\nParent B pays the bill.\n"),
    "T10-mixed-1": (b"Parent A pays the rent.\r\nParent B pays the bill.\nThe exchange is at school.\r\n",
                    b"Parent A pays the rent.\nParent B pays the bill.\r\nThe exchange is at school.\r\n"),
    "T10-mixed-2": (b"Parent A pays the rent.\r\nParent B pays the bill.\nThe exchange is at school.\r\n",
                    b"Parent A pays the rent.\r\nParent B pays the bill.\r\nThe exchange is at school.\n"),
    "T11-bom": (b"Parent A pays the rent.\n", b"\xef\xbb\xbfParent A pays the rent.\n"),
    "T11-none-lf": (b"abc", b"abc\n"),
    "T11-order-edit": (b"Parent A pays the rent.\r\nParent B pays the bill.\n\nThe exchange is at school.\n",
                       b"Parent A pays the rent.\nParent B pays the bill.\r\n\nThe exchange is at the school.\n"),
    "T11-new-kind": (b"Parent A pays the rent.\n", b"Parent A pays the rent.\n\nParent B pays the bill.\r\n"),
    "T12": ("Parent A keeps the agree" + ZWSP + "ment for the children.\n",
            "Parent A keeps the agreement for the children.\n"),
    "T13": ("Parent A met at the caf" + E_ACUTE + ".\n", "Parent A met at the cafe" + ACUTE + ".\n"),
    "T14": ("Parent A's turn is on Friday.\n", "Parent A" + CURLY + "s turn is on Friday.\n"),
    "T15": ("Parent A pays on Friday.\n", "Parent A pays on friday.\n"),
    "T16": ("Parent A has the children on **Friday**\n", "Parent A has the children on Friday\n"),
    "T17": ("Parent A pays rent.\n", "Parent A pays rent.\n".replace("Parent", "P" + CYRILLIC_A + "rent")),
    "T18": (paragraphs(PA, PB, PC), paragraphs(PB, PC, PA)),
    "T19-esc": ("Parent A said hello.\n", "Parent A said hel\x1blo" + RLO + ".\n"),
    "T19-quote": ('Parent A said "hello".\n', 'Parent A said "goodbye".\n'),
    "T19-lt": ("Parent A has <U+200B> today.\n", "Parent A has today.\n"),
    "T19-ff": ("Parent A\x0cpays" + LINE_SEP + "the rent.\n", "Parent A pays the rent.\n"),
    "T29": token_pair(*T29),
    "T29-extras": token_pair(*T29, extras=True),
    "T30": token_pair(*T30),
    "T30-extras": token_pair(*T30, extras=True),
    "T31": token_pair(*T31),
    "T31-extras": token_pair(*T31, extras=True),
    "T32": token_pair(*T32, at_start=True),
    "T32-extras": token_pair(*T32, at_start=True, extras=True),
    "T34": t34_pair(),
}

# Texts the T20 edits start from; "a" is there so that some edits leave a refused file.
T20_BASES = (
    "a",
    "Parent A pays the rent.\n",
    "Parent A pays the rent.\r\nParent B pays the bill.\n\n\nThe exchange is at school.\n",
    "Parent A\tpays the rent on March 3.\n\n  Parent B drops them off at the school.",
)


def spec_text():
    return SPEC.read_text(encoding="utf-8")


def spec_notes():
    return [text for _, text in re.findall(r"^- N(\d): (.*)$", spec_text(), re.M)]


def spec_help():
    return re.search(r"### 3\.4 Help text.*?```text\n(.*?)\n```", spec_text(), re.S).group(1)


def spec_identity_line():
    line = re.search(r"identity line `(family-law-toolkit v<version>[^`]*)`", spec_text()).group(1)
    return line.replace("<version>", __version__)


def spec_listed_phrases():
    line = re.search(r"^- It never uses any of these words or phrases, as whole words, in any case: (.*)$",
                     spec_text(), re.M).group(1)
    return [phrase.strip() for phrase in re.split(r"[,;] ", line.rstrip("."))]


def render(old, new, old_path="old.txt", new_path="new.txt"):
    old, new = as_bytes(old), as_bytes(new)
    differences.check(old)
    differences.check(new)
    return report.render_report(differences.compare(old, new), old_path, new_path)


def page_free_lines(text):
    """The report's lines without the identity line and blank line that open each page."""
    lines = text.replace("\f", "\n").split("\n")
    assert lines.pop() == ""
    kept, skip = [], 0
    for line in lines:
        if skip:
            skip -= 1
            assert line == "" or line == spec_identity_line()
            continue
        if line == spec_identity_line():
            skip = 1
            continue
        kept.append(line)
    return kept


def unwrap(lines):
    """Join each wrapped continuation line (seven spaces) onto the line before it."""
    out = []
    for line in lines:
        if line.startswith("       ") and out:
            out[-1] += " " + line.strip()
        else:
            out.append(line)
    return out


def difference_lines(old, new, old_path="old.txt", new_path="new.txt"):
    """The unwrapped lines of the Differences section for two texts."""
    lines = unwrap(page_free_lines(render(old, new, old_path, new_path)))
    return lines[lines.index("Differences") + 1:lines.index("Notes") - 1]


class FakeStream:
    """A text stream with a binary buffer; fail_after_bytes makes the write raise after
    that many bytes have gone in (0: before any byte)."""

    def __init__(self, fail_after_bytes=None):
        self.buffer = io.BytesIO()
        self.fail_after_bytes = fail_after_bytes
        outer = self

        def write(data):
            if outer.fail_after_bytes is not None:
                io.BytesIO.write(outer.buffer, data[:outer.fail_after_bytes])
                raise BrokenPipeError(32, "Broken pipe")
            return io.BytesIO.write(outer.buffer, data)

        self.buffer.write = write

    def value(self):
        return self.buffer.getvalue()


def run_main(argv, stdout=None, stderr=None, **patches):
    """Call main in-process; return (exit code, stdout bytes, stderr bytes)."""
    out = stdout if stdout is not None else FakeStream()
    err = stderr if stderr is not None else FakeStream()
    with mock.patch.object(sys, "stdout", out), mock.patch.object(sys, "stderr", err):
        code = cli_main.main(argv)
    return code, out.value(), err.value()


def run_cli(args, cwd):
    """Run the command in a subprocess, bytes out, nothing on standard input."""
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    return subprocess.run(
        [sys.executable, "-m", "family_law_toolkit.compare"] + list(args),
        cwd=cwd, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=60,
    )


class Workdir:
    """A temporary directory with write(name, data) -> path."""

    def __init__(self):
        self._dir = tempfile.TemporaryDirectory()
        self.path = self._dir.name

    def write(self, name, data):
        target = os.path.join(self.path, name)
        with open(target, "wb") as handle:
            handle.write(as_bytes(data))
        return target

    def cleanup(self):
        self._dir.cleanup()
