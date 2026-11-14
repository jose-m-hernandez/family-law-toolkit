#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Render GitHub-style markdown pipe tables to a landscape US Letter PDF.

Fails loudly (distinct exit codes, see README.md). Python 3.9 compatible.
Uses only the standard library, reportlab and pypdf. No network, no logging
of input content except the output PDF and stderr error messages.
"""
import argparse
import io
import os
import re
import sys
import tempfile
import unicodedata
from xml.sax.saxutils import escape

EXIT_OK, EXIT_USAGE, EXIT_MALFORMED, EXIT_UNWRITABLE, EXIT_UNEXPECTED = 0, 2, 3, 4, 5

SEP_RE = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")  # closing #s only after a space
STRICT_SEP_CELL = re.compile(r":?-{3,}:?$")
FONT_DIR = "/System/Library/Fonts/Supplemental/"
ZWSP = "\u200b"
FONT_FLOOR = 6.0  # smallest size a table is shrunk to so that no word is broken (README: sizes 4-30, default 9)
FONT_STEP = 0.5


class ToolError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------- parsing
def split_row(line):
    """Split a pipe row into cells. `\\|` is a literal pipe."""
    s = line.strip()
    cells, cur, i = [], [], 0
    if s.startswith("|"):
        s = s[1:]
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    last = "".join(cur).strip()
    # a trailing unescaped pipe leaves an empty final fragment: drop it
    if not (line.strip().endswith("|") and not line.strip().endswith("\\|")
            and last == ""):
        cells.append(last)
    return cells


# ------------------------------------------------------------------ fonts
_FONTS = {}


def load_fonts():
    """Register a system TrueType family (already on disk; never downloaded)."""
    if _FONTS:
        return _FONTS
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    regular = None
    for name in ("Arial Unicode.ttf", "Arial.ttf"):
        if os.path.isfile(FONT_DIR + name):
            regular = FONT_DIR + name
            break
    if regular is None:
        raise ToolError(EXIT_UNEXPECTED, "no system TrueType font found (Arial Unicode.ttf or Arial.ttf)")

    def reg(face, path):
        pdfmetrics.registerFont(TTFont(face, path))
        return set(pdfmetrics.getFont(face).face.charToGlyph)

    _FONTS["reg"] = {"name": "MTP-Reg", "cmap": reg("MTP-Reg", regular)}
    bold = FONT_DIR + "Arial Bold.ttf"
    if os.path.isfile(bold):
        _FONTS["bold"] = {"name": "MTP-Bold", "cmap": reg("MTP-Bold", bold)}
    else:
        _FONTS["bold"] = _FONTS["reg"]
    code = FONT_DIR + "Courier New.ttf"
    if os.path.isfile(code):
        _FONTS["code"] = {"name": "MTP-Code", "cmap": reg("MTP-Code", code)}
    else:
        _FONTS["code"] = _FONTS["reg"]
    pdfmetrics.registerFontFamily("MTP-Reg", normal="MTP-Reg", bold=_FONTS["bold"]["name"],
                                  italic="MTP-Reg", boldItalic=_FONTS["bold"]["name"])
    _FONTS["file"] = os.path.basename(regular)
    from reportlab import rl_config
    rl_config.canvas_basefontname = "MTP-Reg"  # no built-in Helvetica anywhere in the file
    return _FONTS


def covered(text, face):
    cm = load_fonts()[face]["cmap"]
    return all(ch == ZWSP or ch.isspace() or ord(ch) in cm for ch in text)


SHAPING_RE = re.compile(r"^(DEVANAGARI|BENGALI|GURMUKHI|GUJARATI|TAMIL|TELUGU|KANNADA|MALAYALAM|"
                        r"THAI|LAO|KHMER|MYANMAR|TIBETAN|SINHALA|ARABIC|HEBREW|SYRIAC)\b")
RTL_SCRIPTS = ("ARABIC", "HEBREW", "SYRIAC")


def check_text(text, where):
    """Exit 3 (file:line, codepoint named) for anything that cannot print faithfully."""
    cm = load_fonts()["reg"]["cmap"]
    for ch in text:
        if ch == ZWSP:
            continue
        sm = SHAPING_RE.match(unicodedata.name(ch, ""))
        if sm:
            why = ("right-to-left text not supported" if sm.group(1) in RTL_SCRIPTS
                   else "needs letter shaping or reordering, not supported")
            raise ToolError(EXIT_MALFORMED, "%s: character U+%04X (%s script): %s; "
                            "refusing to render it wrongly" % (where, ord(ch), sm.group(1), why))
        cat = unicodedata.category(ch)
        if cat in ("Cc", "Cf", "Cs", "Co", "Cn"):
            raise ToolError(EXIT_MALFORMED,
                            "%s: control/invisible character U+%04X is not allowed; "
                            "refusing to drop or guess" % (where, ord(ch)))
        if cat == "Zs":
            continue  # a space of some width; the line breaker treats it as whitespace
        if ord(ch) not in cm:
            raise ToolError(EXIT_MALFORMED,
                            "%s: character U+%04X is not in the PDF font (%s); refusing to drop it"
                            % (where, ord(ch), load_fonts()["file"]))


# ---------------------------------------------------------------- parsing
def split_row(line):
    """Split a pipe row into cells. `\\|` is a literal pipe."""
    s = line.strip()
    cells, cur, i = [], [], 0
    if s.startswith("|"):
        s = s[1:]
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    last = "".join(cur).strip()
    # a trailing unescaped pipe leaves an empty final fragment: drop it
    if not (line.strip().endswith("|") and not line.strip().endswith("\\|")
            and last == ""):
        cells.append(last)
    return cells


def aligns_of(sep_cells):
    out = []
    for c in sep_cells:
        c = c.strip()
        out.append(1 if c.startswith(":") and c.endswith(":") else 2 if c.endswith(":") else 0)
    return out


def inside_sep(line):
    """A real delimiter row met inside a table (every cell >= 3 hyphens; `| - |` is data)."""
    st = line.strip()
    return bool(SEP_RE.match(st)) and all(STRICT_SEP_CELL.match(c) for c in split_row(line))


def segments(text, markup):
    """[(kind, text)], kind n/b/c. Literal unless markup: then **bold** and `code`
    only under flanking (opener followed by non-space, closer preceded by non-space,
    inner text has a letter or digit; ** runs must be exactly two)."""
    if not markup:
        return [("n", text)]
    out, buf, i, n = [], [], 0, len(text)

    def flush():
        if buf:
            out.append(("n", "".join(buf)))
            del buf[:]

    while i < n:
        ch = text[i]
        if ch == "*":
            j = i
            while j < n and text[j] == "*":
                j += 1
            if j - i == 2 and j < n and not text[j].isspace():
                k = j
                found = None
                while True:
                    k = text.find("**", k)
                    if k < 0:
                        break
                    run_end = k
                    while run_end < n and text[run_end] == "*":
                        run_end += 1
                    if run_end - k == 2 and not text[k - 1].isspace() and k > j \
                            and any(c.isalnum() for c in text[j:k]):
                        found = k
                        break
                    k = run_end
                if found is not None:
                    flush()
                    out.append(("b", text[j:found]))
                    i = found + 2
                    continue
            buf.append(text[i:j])
            i = j
            continue
        if ch == "`" and i + 1 < n and not text[i + 1].isspace() and text[i + 1] != "`":
            k = i + 1
            found = None
            while True:
                k = text.find("`", k)
                if k < 0:
                    break
                if not text[k - 1].isspace() and text[k - 1] != "`" and text[k + 1:k + 2] != "`" \
                        and any(c.isalnum() for c in text[i + 1:k]):
                    found = k
                    break
                k += 1
            if found is not None:
                flush()
                out.append(("c", text[i + 1:found]))
                i = found + 1
                continue
        buf.append(ch)
        i += 1
    flush()
    return out


def plain(text, markup):
    return "".join(t for _, t in segments(text, markup))


def inline(text, markup=False):
    """Return (reportlab markup, plain text)."""
    fonts = load_fonts()
    parts = []
    for kind, t in segments(text, markup):
        if kind == "b" and covered(t, "bold"):
            parts.append("<b>%s</b>" % escape(t))
        elif kind == "c" and covered(t, "code"):
            parts.append('<font name="%s">%s</font>' % (fonts["code"]["name"], escape(t)))
        else:
            parts.append(escape(t))
    return "".join(parts), plain(text, markup)


def parse(text, path, markup=False):
    """Return blocks: ('h', level, text, lineno) | ('p', text, lineno) |
    ('t', header, rows, lineno, [row linenos], [alignments])."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks, para, para_start, i, n = [], [], 0, 0, len(lines)

    def chk(t, where):
        check_text(plain(t, markup), where)

    def flush():
        if para:
            blocks.append(("p", " ".join(para), para_start))
            del para[:]

    while i < n:
        line = lines[i].replace("\t", " ")
        st = line.strip()
        if not st:
            flush()
            i += 1
            continue
        if "|" in st and i + 1 < n and "|" in lines[i + 1] \
                and SEP_RE.match(lines[i + 1].strip()):
            flush()
            header = split_row(line)
            sep = split_row(lines[i + 1])
            if len(sep) != len(header):
                raise ToolError(EXIT_MALFORMED,
                                "%s:%d: separator row has %d cells, header has %d"
                                % (path, i + 2, len(sep), len(header)))
            rows, nums, j = [], [], i + 2
            while j < n:
                rl = lines[j].replace("\t", " ")
                if not rl.strip() or "|" not in rl:
                    break  # blank line or a line with no pipe ends the table
                if inside_sep(rl):
                    raise ToolError(EXIT_MALFORMED,
                                    "%s:%d: separator row inside a table; "
                                    "add a blank line between tables" % (path, j + 1))
                cells = split_row(rl)
                if len(cells) != len(header):
                    raise ToolError(EXIT_MALFORMED,
                                    "%s:%d: row has %d cells, header has %d"
                                    % (path, j + 1, len(cells), len(header)))
                rows.append(cells)
                nums.append(j + 1)
                j += 1
            for k, cells in enumerate([header] + rows):
                ln = i + 1 if k == 0 else nums[k - 1]
                for c in cells:
                    chk(c, "%s:%d" % (path, ln))
            blocks.append(("t", header, rows, i + 1, nums, aligns_of(sep)))
            i = j
            continue
        if st.startswith("|"):
            raise ToolError(EXIT_MALFORMED,
                            "%s:%d: line starts with '|' but is not part of a table "
                            "(a table needs a header row, then a separator row, with no blank "
                            "line inside it); not rendered as a paragraph" % (path, i + 1))
        m = HEADING_RE.match(st)
        if m:
            flush()
            chk(m.group(2), "%s:%d" % (path, i + 1))
            blocks.append(("h", len(m.group(1)), m.group(2), i + 1))
        else:
            chk(st, "%s:%d" % (path, i + 1))
            if not para:
                para_start = i + 1
            para.append(st)
        i += 1
    flush()
    return blocks


# -------------------------------------------------------------- rendering
def build_pdf(blocks, title, font_size, total_pages, markup=False, path=None):
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle

    pagesize = landscape(letter)
    margin = 0.6 * inch
    avail = pagesize[0] - 2 * margin
    fonts = load_fonts()
    REG, BOLD = fonts["reg"]["name"], fonts["bold"]["name"]
    body = ParagraphStyle("b", fontName=REG, fontSize=font_size,
                          leading=font_size * 1.25, spaceAfter=font_size * 0.6)
    # splitLongWords=0: a run of characters with no whitespace is never broken. Column widths
    # are sized so each column holds its longest such token (see plan_table).
    cell = ParagraphStyle("c", parent=body, spaceAfter=0, splitLongWords=0)
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.platypus.paragraph import split as layout_split
    from reportlab.platypus import CondPageBreak

    class KeepBreak(CondPageBreak):
        # zero-size and space-transparent: the paragraph spacing around it is exactly what it
        # would be without it (a plain CondPageBreak would add 5.4 pt before a heading)
        _ZEROSIZE = 1
        _SPACETRANSFER = True

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=pagesize, leftMargin=margin, rightMargin=margin,
                            topMargin=margin, bottomMargin=0.7 * inch,
                            title=title or "", author="", creator="md_table_pdf")
    frame_h = doc.height - 12  # the default frame pads 6 pt top and bottom

    def bold_face(text):
        # bold where the bold face has every glyph, else the regular face (never drop a glyph)
        return BOLD if covered(plain(text, markup), "bold") else REG

    def P(text, style, face=None, align=None):
        kw = {}
        if face:
            kw["fontName"] = face
        if align:
            kw["alignment"] = align
        if kw:
            style = ParagraphStyle("x", parent=style, **kw)
        return Paragraph(inline(text, markup)[0], style)

    def head_style(lvl, keep=1):
        sz = font_size + max(7 - 2 * lvl, 0) + (1 if lvl < 6 else 0)
        return ParagraphStyle("h%d" % lvl, parent=body, fontSize=sz, leading=sz * 1.2,
                              spaceBefore=font_size, keepWithNext=keep)

    def heads_into_table(k):
        """True if block k (a heading) is followed, through further headings only, by a table."""
        while k < len(blocks) and blocks[k][0] == "h":
            k += 1
        return k < len(blocks) and blocks[k][0] == "t"

    ttl = ParagraphStyle("t", parent=body, fontSize=font_size + 7,
                         leading=(font_size + 7) * 1.2, spaceAfter=font_size)

    def token_width(tok, faces, fs):
        return max(stringWidth(tok, f, fs) for f in faces)

    def plan_table(tno, b):
        """Return (font size, column widths) for table `b`.
        Each column's minimum width is its longest unbreakable token (as the line breaker
        splits: whitespace only) plus the 8 pt of cell padding. If the minimums do not fit
        the page width the table's font is reduced in FONT_STEP steps to FONT_FLOOR (never
        below the requested size if that is already smaller); past that, exit 3."""
        header, rows = b[1], b[2]
        nums = [b[3]] + list(b[4])
        ncol = len(header)
        weights = []
        for c in range(ncol):
            col = [header[c]] + [r[c] for r in rows]
            longest = max(len(plain(x, markup)) for x in col)
            word = max(len(w) for x in col for w in (plain(x, markup).split() or [""]))
            weights.append(max(min(longest, 80), min(word, 30), 4))
        tot = float(sum(weights))
        minw = 0.45 * inch
        base = [max(minw, avail * w / tot) for w in weights]
        scale = avail / sum(base)
        base = [w * scale for w in base]

        # tokens per column with the faces they may print in
        body_faces = [REG, BOLD, fonts["code"]["name"]] if markup else [REG]
        toks = [[] for _ in range(ncol)]  # (token, faces, source line)
        for ri, row in enumerate([header] + list(rows)):
            for c, x in enumerate(row):
                faces = ([bold_face(x)] + ([REG, BOLD, fonts["code"]["name"]] if markup else [])
                         ) if ri == 0 else body_faces
                for tk in layout_split(plain(x, markup)):
                    if tk:
                        toks[c].append((tk, faces, nums[ri]))
        fs = font_size
        floor = min(FONT_FLOOR, font_size)
        while True:
            req = [max([token_width(tk, fc, fs) for tk, fc, _ in col] or [0.0]) + 8 + 0.5
                   for col in toks]
            if sum(req) <= avail:
                break
            if fs <= floor + 1e-9:
                big = max(((len(tk), ln, c) for c, col in enumerate(toks) for tk, _, ln in col),
                          key=lambda z: z[0])
                raise ToolError(
                    EXIT_MALFORMED,
                    "%s:%d: table %d: longest unbreakable token is %d characters (column %d); "
                    "the columns' minimum widths total %.0f pt but the page allows %.0f pt, even at "
                    "the minimum table font size of %g pt; refusing to break the token"
                    % (path or "input", big[1], tno, big[0], big[2] + 1, sum(req), avail, floor))
            fs = max(floor, fs - FONT_STEP)
        if all(base[c] >= req[c] for c in range(ncol)):
            return fs, base
        fixed = {}
        while True:
            free = [c for c in range(ncol) if c not in fixed]
            if not free:
                s = sum(fixed.values())
                return fs, [fixed[c] * avail / s for c in range(ncol)]
            rest = avail - sum(fixed.values())
            ftot = float(sum(base[c] for c in free))
            new = {c: rest * base[c] / ftot for c in free}
            bad = [c for c in free if new[c] < req[c]]
            if not bad:
                new.update(fixed)
                return fs, [new[c] for c in range(ncol)]
            for c in bad:
                fixed[c] = req[c]

    story, rows_total, tables = [], 0, 0
    kinds = []      # parallel to story: "h", "p", "t" or "x" (spacer / title)
    first_rows = {}   # story index of a table -> height of its header row + first body row
    if title:
        story.append(P(title, ttl, bold_face(title)))
        kinds.append("x")
    for bi, b in enumerate(blocks):
        if b[0] == "h":
            story.append(P(b[2], head_style(b[1], 0 if heads_into_table(bi) else 1),
                           bold_face(b[2])))
            kinds.append("h")
        elif b[0] == "p":
            story.append(P(b[1], body))
            kinds.append("p")
        else:
            header, rows = b[1], b[2]
            aligns = b[5] if len(b) > 5 else [0] * len(header)
            tables += 1
            rows_total += len(rows)
            tfs, widths = plan_table(tables, b)
            tcell = cell if tfs == font_size else ParagraphStyle(
                "c%g" % tfs, parent=cell, fontSize=tfs, leading=tfs * 1.25)
            if tfs != font_size and total_pages == "?":  # first of the two passes only
                sys.stderr.write("note: table %d set at %g pt (requested %g pt) so that no "
                                 "word is broken across lines\n" % (tables, tfs, font_size))
            data = [[P(h, tcell, bold_face(h), aligns[k]) for k, h in enumerate(header)]]
            for r in rows:
                data.append([P(x, tcell, None, aligns[k]) for k, x in enumerate(r)])
            t = LongTable(data, colWidths=widths, repeatRows=1)
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E0E0E0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            t.wrap(avail, 10 ** 6)  # fills t._rowHeights at the real column widths
            rh = t._rowHeights
            first_rows[len(story)] = rh[0] + (rh[1] if len(rh) > 1 else 0)
            story.append(t)
            kinds.append("t")
            story.append(Spacer(1, font_size))
            kinds.append("x")

    # Keep-with-next for a heading chain that is followed directly by a table. Reportlab's
    # keepWithNext wraps heading + the WHOLE table in KeepTogether, which pushes the table to
    # the next page whenever it is taller than the space left (the cause of the wasted first
    # page). Instead, break the page only if the chain plus the table's header row and first
    # body row do not fit in the space left; otherwise the table starts where it is and splits
    # row by row (header repeats). A chain is the headings in a row; it is measured once, at
    # its first heading.
    out, i = [], 0
    while i < len(story):
        if kinds[i] == "h" and (i == 0 or kinds[i - 1] != "h"):
            j, need = i, 0.0
            while j < len(story) and kinds[j] == "h":
                st = story[j].style
                # the frame collapses this heading's space-before against the previous
                # flowable's space-after, so only the excess is needed
                prev_sa = getattr(getattr(story[j - 1], "style", None), "spaceAfter", 0) if j else 0
                need += (story[j].wrap(avail, 10 ** 6)[1] + max(st.spaceBefore - prev_sa, 0)
                         + st.spaceAfter)
                j += 1
            if j < len(story) and kinds[j] == "t":
                need += first_rows[j]
                out.append(KeepBreak(min(need, frame_h - 1)))
        out.append(story[i])
        i += 1
    story = out

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(REG, 8)
        canvas.drawCentredString(pagesize[0] / 2.0, 0.35 * inch,
                                 "page %d of %s" % (doc.page, total_pages))
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue(), doc.page, tables, rows_total


def render(blocks, title, font_size, markup=False, path=None):
    _, pages, _, _ = build_pdf(blocks, title, font_size, "?", markup, path)
    data, pages2, tables, rows = build_pdf(blocks, title, font_size, pages, markup, path)
    if pages2 != pages:
        raise RuntimeError("page count changed between passes")
    return data, pages, tables, rows


def _tokens(text):
    return text.replace(ZWSP, "").split()


def _match_at(stream, skip, j, toks):
    """Match one cell's tokens as whole tokens starting at stream[j]; return end or None.
    A long word the layout split across lines may span several stream tokens."""
    for t in toks:
        if j >= len(stream) or j in skip:
            return None
        if stream[j] == t:
            j += 1
            continue
        if len(t) >= 4 and t.startswith(stream[j]):
            k, acc = j, ""
            while k < len(stream) and k not in skip and len(acc) < len(t):
                acc += stream[k]
                k += 1
            if acc == t:
                j = k
                continue
        return None
    return j


def verify(pdf_bytes, blocks, pages, title=None, markup=False):
    """Ordered, token-boundary check. Page text is read back in page order (footers and the
    repeated header rows at the top of continuation pages removed, both known because this
    tool placed them); then title, headings, paragraphs and every table cell are walked in
    document order and each must be found, as whole tokens, after the previous match."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(pdf_bytes))
    if len(reader.pages) != pages:
        raise ToolError(EXIT_UNEXPECTED, "verification failed: page count mismatch")
    stream, starts = [], []
    for k, pg in enumerate(reader.pages, 1):
        lines = [ln for ln in (pg.extract_text() or "").split("\n") if ln.strip()]
        foot = "page %d of %d" % (k, pages)
        if lines and lines[0].strip() == foot:
            lines = lines[1:]
        elif lines and lines[-1].strip() == foot:
            lines = lines[:-1]
        else:
            raise ToolError(EXIT_UNEXPECTED, "verification failed: footer missing on page %d" % k)
        starts.append(len(stream))
        for ln in lines:
            stream.extend(_tokens(ln))

    items = []  # (tokens, header tokens of owning table or None for non-body items)
    if title:
        items.append((_tokens(plain(title, markup)), None))
    for b in blocks:
        if b[0] == "h":
            items.append((_tokens(plain(b[2], markup)), None))
        elif b[0] == "p":
            items.append((_tokens(plain(b[1], markup)), None))
        else:
            htoks = [t for c in b[1] for t in _tokens(plain(c, markup))]
            for c in b[1]:
                items.append((_tokens(plain(c, markup)), None))
            for r in b[2]:
                for c in r:
                    items.append((_tokens(plain(c, markup)), htoks))

    skips = {}

    def skip_for(htoks):
        key = tuple(htoks)
        if key not in skips:
            sk = set()
            for s0 in starts[1:]:
                if htoks and stream[s0:s0 + len(htoks)] == htoks:
                    sk.update(range(s0, s0 + len(htoks)))
            skips[key] = sk
        return skips[key]

    pos = 0
    for toks, htoks in items:
        if not toks:
            continue
        sk = skip_for(htoks) if htoks else set()
        end = None
        for j in range(pos, len(stream)):
            end = _match_at(stream, sk, j, toks)
            if end is not None:
                break
        if end is None:
            raise ToolError(EXIT_UNEXPECTED,
                            "verification failed: table cell text missing from PDF")
        pos = end


# -------------------------------------------------------------------- cli
def run(args):
    if args.out_pos is not None:
        if args.output is not None:
            raise ToolError(EXIT_USAGE, "give the output as a second argument or with -o, not both")
        if not args.out_pos.lower().endswith(".pdf"):
            raise ToolError(EXIT_USAGE, "second argument must be an output path ending in .pdf")
        args.output = args.out_pos
    inp = os.path.abspath(args.input)
    out = os.path.abspath(args.output) if args.output else os.path.splitext(inp)[0] + ".pdf"
    if not 4 <= args.font_size <= 30:
        raise ToolError(EXIT_USAGE, "--font-size must be between 4 and 30")
    if args.title:
        try:
            check_text(plain(args.title, args.markup), "--title")
        except ToolError as e:
            raise ToolError(EXIT_USAGE, "--title: " + e.message)
    if out == inp or (os.path.exists(out) and os.path.exists(inp) and os.path.samefile(out, inp)):
        raise ToolError(EXIT_USAGE, "refusing to overwrite the input file")
    try:
        with open(inp, "rb") as f:
            raw = f.read()
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        raise ToolError(EXIT_USAGE, "cannot read input %s (%s)" % (inp, type(e).__name__))
    blocks = parse(text, inp, args.markup)
    if not any(b[0] == "t" for b in blocks):
        raise ToolError(EXIT_USAGE, "no markdown table found in %s" % inp)
    outdir = os.path.dirname(out)
    if os.path.isdir(out) or not os.path.isdir(outdir) or not os.access(outdir, os.W_OK | os.X_OK):
        raise ToolError(EXIT_UNWRITABLE, "output not writable: %s" % out)

    data, pages, tables, rows = render(blocks, args.title, args.font_size, args.markup, inp)
    verify(data, blocks, pages, args.title, args.markup)

    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix=".md_table_pdf-", suffix=".tmp", dir=outdir)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, out)
        tmp = None
    except OSError as e:
        raise ToolError(EXIT_UNWRITABLE, "output not writable: %s (%s)" % (out, type(e).__name__))
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
    print(out)
    print("%d tables, %d body rows, %d pages" % (tables, rows, pages))
    return EXIT_OK


def main(argv=None):
    ap = argparse.ArgumentParser(prog="md_table_pdf.py",
                                 description="Render markdown pipe tables to a landscape Letter PDF.")
    ap.add_argument("input")
    ap.add_argument("out_pos", nargs="?", metavar="OUT.pdf",
                    help="output path; same as -o OUT.pdf (not allowed together with -o; must end in .pdf)")
    ap.add_argument("-o", "--output")
    ap.add_argument("--title")
    ap.add_argument("--font-size", type=float, default=9.0)
    ap.add_argument("--markup", action="store_true",
                    help="render **bold** and `code` (flanked, with a letter or digit inside). "
                         "This removes ** and backticks when they form markers, so literal "
                         "mode is the default for exactly that reason")
    try:
        args = ap.parse_args(argv)  # argparse exits 2 on usage errors
        return run(args)
    except ToolError as e:
        sys.stderr.write("error: %s\n" % e.message)
        return e.code
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else EXIT_USAGE
    except BaseException as e:  # fail closed; type name only, no input content
        sys.stderr.write("error: unexpected %s\n" % type(e).__name__)
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    sys.exit(main())
