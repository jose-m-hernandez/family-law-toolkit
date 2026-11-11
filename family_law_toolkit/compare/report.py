# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Plain-text comparison report (spec section 5).

Every page starts with the identity line. render_report(result, old_path,
new_path) is the one way to produce report text.
"""

import textwrap
import unicodedata

from family_law_toolkit import TOOLKIT_NAME, __version__
from family_law_toolkit.compare.differences import DETAIL_LINE, describe_line_ends

IDENTITY_LINE = TOOLKIT_NAME + " v" + __version__ + " — not certified for court filing"
EDUCATIONAL_LINE = "Educational; not legal advice; not certified for court filing; consult counsel."
PAGE_LINES = 60
BODY_LINES_PER_PAGE = PAGE_LINES - 2  # the identity line and one blank line

NOTES = (
    'This report lists differences in the text of the two files. It does not say whether any difference matters.',
    'It reads both files as plain text. Fonts, bold, italics, page layout, checked boxes and form fields are not compared, and Markdown markup is read as ordinary characters.',
    'Moves are not tracked: a paragraph that moved, or the paragraphs it moved past, may be listed as only in old at one place and only in new at another.',
    '"Old" and "new" are the labels you gave. This tool does not check which file is older, who changed either file, when, or whether either was filed or served.',
    'This report can repeat text from both files and prints their paths as you typed them. Keep it as private as the files.',
    "Paragraph and line numbers in this report count the paragraphs and lines of each file as saved (lines end at LF, CR or CRLF). They are not the paper's own numbered paragraphs, or the page and line numbers of a printed or filed copy.",
    'Spacing and hidden or look-alike characters are not compared inside a Differs entry. Blank lines are not compared at, just before or just after a Differs, Only in old or Only in new entry, except at the end of a file. When both files use the same kinds of line end and their text differs elsewhere, where the line ends sit is not compared.',
    'If a file was made from a PDF or a form, checked boxes, form fields, stamps and signatures may be missing from it. This report covers only the text in the two files.',
)

_LABELS = {
    "differs": "Differs",
    "only_old": "Only in old",
    "only_new": "Only in new",
    "hidden": "Hidden or look-alike characters",
    "spacing_in": "Spacing in the paragraph",
    "spacing_before": "Spacing before the paragraph",
    "file": "File",
}


def escape(text, quote=False, space=False, ascii_only=False):
    """Write control, hidden and surrogate characters and `<` as <U+XXXX> (5.3); `quote`
    also escapes a double quote, `space` any whitespace but a space, `ascii_only` every
    character outside printable ASCII."""
    out = []
    for c in text:
        if (
            unicodedata.category(c) in ("Cc", "Cf", "Cs")
            or c == "<"
            or (quote and c == '"')
            or (space and c.isspace() and c != " ")
            or (ascii_only and not " " <= c <= "~")
        ):
            out.append("<U+%04X>" % ord(c))
        else:
            out.append(c)
    return "".join(out)


def _wrap(line, indent=7):
    return textwrap.wrap(
        line, width=78, subsequent_indent=" " * indent, break_long_words=False, break_on_hyphens=False
    )


def paginate(body_lines):
    """Split body lines into pages; each page opens with the identity line."""
    lines = list(body_lines)
    chunks = [
        lines[start:start + BODY_LINES_PER_PAGE]
        for start in range(0, len(lines), BODY_LINES_PER_PAGE)
    ] or [[]]
    return ["\n".join([IDENTITY_LINE, ""] + chunk) for chunk in chunks]


def _count(number, word):
    return "{:,} {}{}".format(number, word, "" if number == 1 else "s")


def _place(side, paras):
    first, last = paras[0], paras[-1]
    numbers = "paragraph %d" % first.number if first is last else "paragraphs %d-%d" % (first.number, last.number)
    lines = "line %d" % first.first if first.first == last.last else "lines %d-%d" % (first.first, last.last)
    return "%s file %s, file %s" % (side, numbers, lines)


def _shown(items, ascii_only):
    groups, current = [], []
    for item in items:
        if item.word is None:
            if current:
                groups.append('"%s"' % " ".join(current))
                current = []
            groups.append("(paragraph break)")
        else:
            current.append(escape(item.piece, quote=True, ascii_only=ascii_only))
    if current:
        groups.append('"%s"' % " ".join(current))
    return " ".join(groups)


def _span(side, items):
    first, last = items[0].line, items[-1].line
    if first == last:
        return "%s file line %d" % (side, first)
    return "%s file lines %d-%d" % (side, first, last)


def _word_line(diff):
    def sides(ascii_only):
        if diff.old and diff.new:
            return "old %s, new %s" % (_shown(diff.old, ascii_only), _shown(diff.new, ascii_only))
        if diff.old:
            return "only in old " + _shown(diff.old, ascii_only)
        return "only in new " + _shown(diff.new, ascii_only)

    spans = ", ".join(_span(side, items) for side, items in (("old", diff.old), ("new", diff.new)) if items)
    if diff.context:
        context = 'after "%s"' % " ".join(escape(piece, quote=True) for piece in diff.context)
    else:
        context = "at the start of a paragraph"
    line = "     - %s: %s, %s" % (spans, sides(False), context)
    if any(not " " <= c <= "~" for word in diff.old + diff.new if word.piece for c in word.piece):
        line += "; as code points: " + sides(True)
    return _wrap(line)


def _run_line(old, new):
    def side(pieces):
        shown = " ".join(escape(p, quote=True, ascii_only=True) for p in pieces)
        return '"%s"' % shown if pieces else "(nothing)"

    return _wrap("     - old %s, new %s" % (side(old), side(new)))


def _text_lines(label, paras):
    return [
        line for para in paras
        for line in _wrap("     %s: %s" % (label, " ".join(escape(piece) for piece in para.pieces)))
    ]


def _entry_lines(number, entry):
    head = "  %d. %s: " % (number, _LABELS[entry.kind])
    if entry.kind == "file":
        return [head + entry.text]
    if entry.kind in ("only_old", "only_new"):
        side, other = ("old", "new") if entry.kind == "only_old" else ("new", "old")
        word, anchor = entry.anchor
        paras = entry.old or entry.new
        return [head + _place(side, paras) + "; %s %s file paragraph %d" % (word, other, anchor)] + _text_lines(side, paras)
    lines = [head + _place("old", entry.old) + "; " + _place("new", entry.new)]
    if entry.kind == "differs":
        lines += _text_lines("old", entry.old) + _text_lines("new", entry.new)
        if entry.diffs is None:
            return lines + _wrap("     " + DETAIL_LINE)
        for diff in entry.diffs:
            lines += _word_line(diff)
    elif entry.kind == "hidden":
        if entry.runs is None:
            return lines + _wrap("     " + DETAIL_LINE)
        for old, new in entry.runs:
            lines += _run_line(old, new)
    return lines


def _result_line(result):
    if result.identical:
        return "Result: the two files are identical, byte for byte."
    kinds = [entry.kind for entry in result.entries]
    return (
        "Result: the files differ. Differs %d, only in old %d, only in new %d, spacing %d, "
        "hidden or look-alike characters %d, file %d."
        % (
            kinds.count("differs"),
            kinds.count("only_old"),
            kinds.count("only_new"),
            kinds.count("spacing_in") + kinds.count("spacing_before"),
            kinds.count("hidden"),
            kinds.count("file"),
        )
    )


def render_report(result, old_path, new_path):
    """Return the whole report text: pages joined by form feeds, one final LF."""
    body = ["Comparison of two text files", EDUCATIONAL_LINE, "", "Files"]
    for label, option, found, path in (
        ("Old", "--old", result.old, old_path),
        ("New", "--new", result.new, new_path),
    ):
        body += [
            "  %s (%s): %s" % (label, option, escape(path, space=True)),
            "    %s; %s; %s; byte-order mark: %s; line ends: %s"
            % (
                _count(found.size, "byte"),
                _count(found.nlines, "line"),
                _count(len(found.paras), "paragraph"),
                "yes" if found.bom else "no",
                describe_line_ends(found.kinds),
            ),
            "    sha256: " + found.sha256,
        ]
    body += ["", _result_line(result)]
    if result.entries:
        body += ["", "Differences"]
        for number, entry in enumerate(result.entries, 1):
            body += _entry_lines(number, entry)
    body += ["", "Notes"]
    for note in NOTES:
        body += _wrap("  " + note, 2)
    return "\f".join(paginate(body)) + "\n"
