# md-table-pdf

Render markdown pipe tables (with optional `#` headings and paragraphs) to a landscape US Letter PDF.
Python 3.9 stdlib + reportlab + pypdf. No network, no telemetry; input content goes only to the PDF.

    python3 md_table_pdf.py INPUT.md [OUTPUT.pdf | -o OUTPUT.pdf] [--title TEXT] [--font-size N] [--markup]

`INPUT.md OUT.pdf` is identical to `INPUT.md -o OUT.pdf`. Giving both is exit 2, and a positional
output not ending in `.pdf` (any case) is exit 2. Literal remains the default in both forms.
Paths resolve against the current directory. Default output: input's directory and stem, `.pdf`.
On success prints the absolute output path, then `N tables, N body rows, N pages`.
Font size 4-30 (default 9). Every page has a footer "page x of y".

## Exit codes
- 0 success
- 2 usage, missing/unreadable (non-UTF-8) input, no table found, or output equals input (never overwritten)
- 3 malformed input, always with `file:line`: row/separator cell count differs from header; a separator
  row inside a table (back-to-back tables need a blank line between them); a line starting with `|` that
  is not part of a table (including a table continued after a blank line; never rendered as a paragraph);
  a character the font lacks, or a control character or soft hyphen (U+00AD), named by codepoint; an
  unbreakable token that cannot fit the page width even at the 6 pt floor (table number and token length named)
- 4 output not writable (missing dir, permissions, target is a directory)
- 5 unexpected exception (one line, exception type only), or the self-check failed. Includes a row too
  tall for one page.

No failure leaves a PDF or temp file behind (temp file in output dir, then `os.replace`).

## Rendering rules
- **Literal by default**: no markup processing; cell, heading and paragraph text prints exactly as written
  (`*****1234`, `2**10` stay as typed), apart from `\|` -> `|` in cells.
- `--markup` renders `**bold**` and `` `code` `` (bold / Courier New) only when flanked: the opener is followed by
  non-whitespace, the closer is preceded by non-whitespace, the inner text has a letter or digit, and a `**` run
  is exactly two asterisks. So `*****1234` and `p < .05**` stay literal, but `2**10 and 3**2` is bold
  (it meets the rule). Other markdown (links, lists, `<br>`, italics) is always literal.
- A table is a header row, a separator row, then rows. A blank line or a line with no `|` ends it; any line
  containing `|` inside it is a row (even if it starts with `#`). Tables need no outer pipes.
- Alignment from the separator row is honoured: `:---` left, `:---:` centre, `---:` right (header included).
- Headings: closing `#`s are stripped only when preceded by a space (`# Item C#` keeps `C#`).
- Header row repeats on each page. Long text wraps at spaces. **A run of characters with no whitespace
  (a date, `M/DD-MM/DD`, an account number) is never broken**: each column is sized to at least its longest
  such token plus cell padding. If the columns' minimums do not fit the page width, that table's font is
  reduced in 0.5 pt steps to a floor of 6 pt (or the `--font-size` you asked for, if smaller), with a
  `note:` line on stderr; if it still cannot fit, exit 3 naming `file:line`, the table number and the token
  length. Nothing is hyphenated or split silently. (A zero-width space, U+200B, is still a break point.)
- **A heading stays with its table.** A heading (or run of headings) directly above a table moves to the
  next page only if it plus the table's header row and first body row do not fit in the space left;
  otherwise the table starts right under it and continues across pages row by row. No page break is
  forced after a title block, so a first section starts on page 1 when it fits there.
- **Font**: a TrueType file already on the system, never downloaded: `/System/Library/Fonts/Supplemental/Arial Unicode.ttf`,
  else `Arial.ttf` (Arial Bold for bold, Courier New for code spans, where present). U+2011, U+2212,
  U+00A0, U+202F (rendered as a space) and accented letters work with Arial Unicode; with plain Arial.ttf,
  U+2011 exits 3. U+200B passes through. No font file -> exit 5.

## Invariant
Every body row appears in the PDF. After rendering, the tool re-reads the PDF with pypdf in page order,
removes the footers and the header rows it repeated on continuation pages, then walks title, headings,
paragraphs and every table cell in document order: each cell's text must be found as whole tokens after the
previous match (so a footer, a paragraph, a substring of a longer cell or two adjacent cells cannot stand in for
a missing cell). Otherwise exit 5 and no file is written. Tests additionally check with `pdftotext`.

## Limits
- Needs the macOS system font (`Arial Unicode.ttf`, else `Arial.ttf`). On other machines it fails loudly (exit 5).
- Scripts needing letter shaping or reordering (Devanagari, Bengali, Gurmukhi, Gujarati, Tamil, Telugu, Kannada,
  Malayalam, Thai, Lao, Khmer, Myanmar, Tibetan, Sinhala, Arabic, Hebrew, Syriac) exit 3 naming the character
  and script; Arabic, Hebrew and Syriac say "right-to-left text not supported".
- A single row taller than a page cannot be split: exit 5.
- Column widths are proportional to content, raised where needed to hold the longest unbreakable token;
  very many columns (>~15) get narrow and may force the table font down to the 6 pt floor or exit 3.
- The self-check is text-based: it proves text is present and in order, not that the layout looks right.
  A word the layout splits across lines (>= 4 characters) is matched as consecutive pieces (the layout no
  longer splits words; this is kept as a safety net).
- A heading followed by a paragraph (not directly by a table) stays with that paragraph only; the paragraph
  and the table below it may fall on different pages.
- A table row of only `---` cells (3+ hyphens) is read as a separator; `| - | - |` is data.

## Tests
    python3 -m unittest discover -s tests      # fixtures: make_fixtures.py
