# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""What counts as a difference between two files' text (spec sections 3.2 and 4).

check(data) runs the content checks on one file's bytes; compare(old, new)
compares two byte strings that check() accepted and returns a Result.
"""

import difflib
import hashlib
import re
import unicodedata
from collections import namedtuple

MAX_BYTES = 200000
MATCH_LIMIT = 250000  # one matching, after the shared start and end are set aside (4.4)
SHARED_LIMIT = 500000  # every word or piece matching together, in entry order (4.4)
BOM = b"\xef\xbb\xbf"
# The two fixed detail lines of spec 4.4: Line A for a Differs entry, Line B for a
# Hidden or look-alike characters entry past the matching limit.
DETAIL_LINE = (
    "Detail not shown: this tool's matching limit was reached. The files differ in "
    "the paragraphs this entry names; words, figures and dates that differ inside "
    "them are not listed."
)
DETAIL_LINE_HIDDEN = (
    "Detail not shown: this tool's matching limit was reached. The files differ in "
    "the paragraphs this entry names; hidden or look-alike characters that differ "
    "inside them are not listed."
)

Word = namedtuple("Word", "word line piece")  # a paragraph-break token has word None
Diff = namedtuple("Diff", "old new context")  # one word difference: Words, Words, pieces


class Refused(ValueError):
    """A file the content checks refuse; reason is not-plain-text, not-utf-8 or no-text."""

    def __init__(self, reason):
        ValueError.__init__(self, reason)
        self.reason = reason


class TooManyParagraphs(ValueError):
    """The paragraph matching would pass its cap (4.4)."""


def check(data):
    """Section 7 rows 6, 7 and 8, in that order."""
    if data.startswith(BOM):
        data = data[3:]
    if b"\x00" in data or data.startswith((b"%PDF-", b"PK\x03\x04")):
        raise Refused("not-plain-text")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("not-utf-8") from None
    if not text or text.isspace():
        raise Refused("no-text")


def describe_line_ends(kinds):
    """`LF`, `CRLF`, `CR`, `none` or `mixed (CRLF 3, LF 28)` (5.2)."""
    counts = [(kind, kinds.count(kind)) for kind in ("CRLF", "LF", "CR") if kind in kinds]
    if not counts:
        return "none"
    if len(counts) == 1:
        return counts[0][0]
    return "mixed (%s)" % ", ".join("%s %d" % count for count in counts)


def _word(piece):
    kept = "".join(c for c in piece if unicodedata.category(c) != "Cf")
    return unicodedata.normalize("NFC", kept)


class _Paragraph:
    def __init__(self, number, first, last, text, lead, lines):
        self.number, self.first, self.last, self.text, self.lead = number, first, last, text, lead
        self.pieces = text.split()
        self.words = []
        for line_number, line in enumerate(lines, first):
            for piece in line.split():
                if _word(piece):
                    self.words.append(Word(_word(piece), line_number, piece))
        self.key = tuple(w.word for w in self.words)
        self.runs = re.split(r"\S+", text)  # whitespace runs, alternating with the pieces


class _File:
    """One file's facts and paragraphs (3.2, 4.1); data has passed check()."""

    def __init__(self, data):
        self.size = len(data)
        self.sha256 = hashlib.sha256(data).hexdigest()
        self.bom = data.startswith(BOM)
        raw = (data[3:] if self.bom else data).decode("utf-8")
        self.kinds = [{"\r\n": "CRLF", "\n": "LF", "\r": "CR"}[k] for k in re.findall(r"\r\n|\r|\n", raw)]
        self.text = raw.replace("\r\n", "\n").replace("\r", "\n")
        lines = self.text.split("\n")
        if self.text.endswith("\n"):
            lines.pop()
        self.nlines = len(lines)
        groups, position = [], 0
        for number, line in enumerate(lines, 1):
            if line and not line.isspace():
                if groups and groups[-1][1] == number - 1:
                    groups[-1][1], groups[-1][3] = number, position + len(line)
                else:
                    groups.append([number, number, position, position + len(line)])
            position += len(line) + 1
        self.paras, previous = [], 0
        for number, (first, last, start, end) in enumerate(groups, 1):
            self.paras.append(_Paragraph(
                number, first, last, self.text[start:end], self.text[previous:start], lines[first - 1:last]
            ))
            previous = end
        self.tail = self.text[previous:]


class Entry:
    """One listed difference; kind is differs, only_old, only_new, hidden, spacing_in,
    spacing_before or file."""

    def __init__(self, kind, **fields):
        self.kind = kind
        self.__dict__.update(fields)


class Result:
    def __init__(self, old, new, identical):
        self.old, self.new, self.identical, self.entries = old, new, identical, []


def _trim(a, b):
    """Lengths of the shared start and of the shared end of the rest."""
    limit = min(len(a), len(b))
    start = 0
    while start < limit and a[start] == b[start]:
        start += 1
    end = 0
    while end < limit - start and a[len(a) - 1 - end] == b[len(b) - 1 - end]:
        end += 1
    return start, end


def _match(a, b, budget):
    """The non-equal opcodes of a against b, or None when a limit would be broken."""
    start, end = _trim(a, b)
    ma, mb = a[start:len(a) - end], b[start:len(b) - end]
    cost = len(ma) * len(mb)
    if cost > MATCH_LIMIT or budget[0] + cost > SHARED_LIMIT:
        return None
    budget[0] += cost
    matcher = difflib.SequenceMatcher(None, ma, mb, autojunk=False)
    return [
        (tag, i1 + start, i2 + start, j1 + start, j2 + start)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]


def _paragraph_opcodes(a, b):
    start, end = _trim(a, b)
    ma, mb = a[start:len(a) - end], b[start:len(b) - end]
    if len(ma) * len(mb) > MATCH_LIMIT:
        raise TooManyParagraphs("too many paragraphs lie between the first and last differences")
    ops = [("equal", 0, start, 0, start)] if start else []
    matcher = difflib.SequenceMatcher(None, ma, mb, autojunk=False)
    ops += [(t, i1 + start, i2 + start, j1 + start, j2 + start) for t, i1, i2, j1, j2 in matcher.get_opcodes()]
    if end:
        ops.append(("equal", len(a) - end, len(a), len(b) - end, len(b)))
    return ops


def _items(paras):
    items = []
    for index, para in enumerate(paras):
        if index:
            items.append(Word(None, para.first, None))
        items.extend(para.words)
    return items


def _differs(old, new, budget):
    old_items, new_items = _items(old), _items(new)
    ops = _match([w.word for w in old_items], [w.word for w in new_items], budget)
    diffs = None
    if ops is not None:
        diffs = []
        for tag, i1, i2, j1, j2 in ops:
            source, at = (old_items, i1) if tag == "delete" else (new_items, j1)
            context, index = [], at - 1
            while index >= 0 and len(context) < 3 and source[index].word is not None:
                context.insert(0, source[index].piece)
                index -= 1
            diffs.append(Diff(old_items[i1:i2], new_items[j1:j2], context))
    return Entry("differs", old=old, new=new, diffs=diffs)


def _pair_entries(old, new, lead_compared, budget):
    entries = []
    if old.pieces != new.pieces:
        ops = _match(old.pieces, new.pieces, budget)
        runs = None if ops is None else [(old.pieces[i1:i2], new.pieces[j1:j2]) for _, i1, i2, j1, j2 in ops]
        entries.append(Entry("hidden", old=[old], new=[new], runs=runs))
    if old.runs != new.runs:
        entries.append(Entry("spacing_in", old=[old], new=[new]))
    if lead_compared and old.lead != new.lead:
        entries.append(Entry("spacing_before", old=[old], new=[new]))
    return entries


def _file_entries(old, new):
    texts = []
    if old.bom != new.bom:
        texts.append("byte-order mark in %s only" % ("old" if old.bom else "new"))
    if set(old.kinds) != set(new.kinds) or (old.text == new.text and old.kinds != new.kinds):
        pairs = list(zip(old.kinds, new.kinds))
        first = next((i for i, (x, y) in enumerate(pairs) if x != y), len(pairs))
        texts.append("line ends: old %s, new %s; first different at file line %d" % (
            describe_line_ends(old.kinds), describe_line_ends(new.kinds), first + 1))
    if old.tail != new.tail:
        texts.append("blank lines or line ends after the last paragraph differ")
    return [Entry("file", text=text) for text in texts]


def compare(old, new):
    """Compare two byte strings that check() accepted (4.2 to 4.4, 5.3's entry order)."""
    old_file, new_file = _File(old), _File(new)
    result = Result(old_file, new_file, old == new)
    if result.identical:
        return result
    ops = _paragraph_opcodes([p.key for p in old_file.paras], [p.key for p in new_file.paras])
    paired = {}
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal":
            paired.update(zip(range(i1, i2), range(j1, j2)))
    budget = [0]
    old_paras, new_paras = old_file.paras, new_file.paras
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                compared = (i == 0 and j == 0) or (i > 0 and paired.get(i - 1) == j - 1)
                result.entries += _pair_entries(old_paras[i], new_paras[j], compared, budget)
        elif tag == "replace":
            result.entries.append(_differs(old_paras[i1:i2], new_paras[j1:j2], budget))
        elif tag == "delete":
            anchor = ("after", j1) if j1 else ("before", 1)
            result.entries.append(Entry("only_old", old=old_paras[i1:i2], new=[], anchor=anchor))
        else:
            anchor = ("after", i1) if i1 else ("before", 1)
            result.entries.append(Entry("only_new", old=[], new=new_paras[j1:j2], anchor=anchor))
    result.entries += _file_entries(old_file, new_file)
    return result
