# Compare drafts: behaviour spec

Status: DRAFT. Not accepted, and nothing is built. Section 11 holds the open questions for this tool's legal reviewer, the General Counsel (GC); a rule marked "pending Q-Cn" can change with the answer.
Date: 2026-11-04.
Revision: draft 11.

Written from requirements only: what a person preparing California family-law paperwork needs when comparing two versions of a document they are writing. Every example and test fixture is invented.

## 1. Purpose

Show a person, in plain text, the differences section 4 defines between the text of two versions of a document (for example, a declaration they wrote and a revised one; which papers are in scope is pending Q-C1), so they can read each difference for themselves. The tool never judges a difference or says what to do about one.

## 2. Scope and non-goals

Phase 1 scope and its build order are pending Q-C1 and Q-C11.

In (phase 1):
- exactly two files, named with `--old` and `--new`, each UTF-8 plain text; Markdown is read as plain text (3.3);
- a comparison by paragraph, then by word, with differences in spacing, line ends, the byte-order mark and code points listed separately (section 4);
- a plain-text report on standard output, and an exit status (section 5).

Out:
- judging a difference: whether it matters, what it means or does, or which version is better;
- suggesting, rewriting, merging or accepting text; writing or changing any file;
- who changed a file, when, or which file is older or came from the other (`old` and `new` are the person's labels);
- formatting: fonts, bold, italics, page layout, headers and footers, rendered Markdown;
- PDF, DOCX, RTF, ODT and images (section 10; DOCX pending Q-C8, PDF Q-C9, the rest Q-C11);
- margin line numbers, and locations given as a page and line (pending Q-C2);
- tracking moved text: matching keeps the longest run of paragraphs in order, so a moved paragraph, or the paragraphs it moved past, may be listed as only in old at one place and only in new at another;
- more than two files, folders, standard input, the network, and any temporary or log file.

## 3. Inputs

The command is `python3 -m family_law_toolkit.compare --old FILE --new FILE` (a working name, settled at release). It needs Python 3.9 or later and the standard library only (for example `argparse`, `difflib`, `os`, `sys`, `textwrap` and `unicodedata`), like the rest of the repository. A Python API mirrors the support tool's `compute()` and `render_report()`, with working names: `check(data)` runs the content checks of section 7 (rows 6 to 8) on one file's bytes; `compare(old, new)` compares two byte strings that `check()` has accepted and returns a result; `render_report(result, old_path, new_path)` renders it, with the two paths as typed. The command runs the other checks and calls `check()` once per file, in the order section 7 gives.

### 3.1 Options

| Option | Meaning |
|---|---|
| `--old FILE` | One version. Required, given exactly once. |
| `--new FILE` | The other version. Required, given exactly once. |
| `-h`, `--help` | Write the help text (3.4) to standard output and exit 0. Reads no file, and wins over every other argument, as in the support command. |

A missing, repeated, unknown or abbreviated option, any other argument, or a `FILE` of `-` is a usage error (section 7). A path that starts with `-` is given as `--old=-notes.txt` or `./-notes.txt`. A repeated option and a `FILE` of `-` each need their own check, because the argument parser keeps the last value of a repeated option and accepts `-` as a value.

### 3.2 Files

- Each path is checked with `os.stat` before it is opened, and must be a regular file, so a folder, device or FIFO is refused without being opened. At most 200,001 bytes are read, and a file may be at most 200,000 bytes; matching work is also capped (4.4).
- A leading UTF-8 byte-order mark is removed and recorded. The rest must be valid UTF-8, decoded strictly. Reason: replacing a bad byte could make two different files read alike and hide a difference.
- The checks in this section run in section 7's table order. A file is refused as not plain text if it holds a NUL byte, if its bytes after any byte-order mark start with `%PDF-` or with the zip signature `PK\x03\x04` (a DOCX file is a zip), or if its name ends in `.pdf`, `.docx`, `.doc`, `.rtf` or `.odt`, in any case. Reason: phase 1 must not compare the bytes of a binary file as if they were words.
- Line ends: each CRLF, then each remaining lone CR, becomes LF, and each file's line ends are recorded by kind, in order. After that, only LF ends a line: a form feed, vertical tab, U+0085, U+2028 or U+2029 inside a line is whitespace, not a line end. Lines are numbered from 1, and a final line end does not start a new line.
- A file that is empty, holds only a byte-order mark, or holds nothing but whitespace (4.1) has no text to compare. `--old` and `--new` naming the same file (`os.path.samefile`) is refused.

### 3.3 Markdown

Read as plain text (N2 says so; pending Q-C5). `#`, `*`, `_`, backticks and link syntax are ordinary characters, so `**Friday**` against `Friday` is a wording difference.

### 3.4 Help text

Draft; the final wording is reviewed before release, and the first line, the "Educational" line and two sentences are pending Q-C5.

```text
usage: python3 -m family_law_toolkit.compare --old FILE --new FILE

Compare the text of two versions of a document
Educational; not legal advice; not certified for court filing; consult counsel.

Required:
  --old FILE
      One version: a plain-text or Markdown file
  --new FILE
      The other version: a plain-text or Markdown file

Each file is read as UTF-8 text, up to 200,000 bytes. PDF and Word files are
not read. "Old" and "new" are your labels; this tool does not check which file
is older.
It lists differences in the text. It does not say whether any difference
matters.

Exit status: 0 the files are identical byte for byte, 1 they differ, 2 the
comparison could not run.
```

## 4. What counts as a difference

### 4.1 Terms

- **Whitespace:** a character for which Python's `str.isspace()` is true.
- **Hidden character:** a character in Unicode category Cf (format characters), such as U+200B ZERO WIDTH SPACE or U+00AD SOFT HYPHEN. Most print as nothing; some invisible characters are in other categories and count as visible (8, known limits).
- **Blank line:** a line that is empty or holds only whitespace. A line holding only hidden characters is not blank.
- **Paragraph:** a longest run of non-blank lines; its text is those lines joined by LF. Its location is its number in its file, from 1, and its first and last line numbers. Its **lead** is all the text between the end of the paragraph before it (or the start of the file) and its first character. The file's **tail** is all the text after the last paragraph.
- **Pieces:** a paragraph's text split on whitespace (`str.split()`), with hidden characters kept. **Words:** for each line, remove the hidden characters, put the rest in Unicode NFC form, and split it on whitespace; each word keeps its line number.
- **Whitespace runs:** the paragraph's text split at each longest run of non-whitespace characters, so that runs and pieces alternate, with an empty run at the start or end where the text has no whitespace there; runs are compared character for character.

Category Cf and NFC come from the running Python's Unicode data, so a character added to Unicode after Python 3.9's version can be reported differently by different Python versions.

### 4.2 Wording

The paragraph lists are matched with `difflib.SequenceMatcher(None, old, new, autojunk=False)`, comparing each paragraph by its tuple of words, after setting aside the paragraphs the two lists share at their start, then those the rest share at their end (those pair as `equal`). Each opcode gives:
- `equal`: paired paragraphs with the same words; 4.3 then checks them;
- `delete`: one **Only in old** entry; `insert`: one **Only in new** entry;
- `replace`: one **Differs** entry. The words of the old run and the new run, with one paragraph-break token between paragraphs (equal only to another paragraph break), are matched the same way, shared start and end set aside, and each opcode other than `equal` is one word difference (5.3).

Case, punctuation and every visible character count: `Friday` and `friday`, a straight and a curly quote, a hyphen and a dash are different words. `autojunk=False` keeps a repeated word or paragraph from being treated as junk, so the result depends only on the two texts (and 4.1's Unicode note).

### 4.3 Differences other than wording

The labels below are pending Q-C3. For each `equal` pair:
- **Code points** differ when the two paragraphs' pieces differ: the words match, but a hidden character, or the same letter written with different code points, differs.
- **Spacing** differs in the paragraph when the two paragraphs' whitespace runs differ, and before it when the two leads differ and the paragraphs before them are themselves an `equal` pair (or both paragraphs are first in their files). A lead next to an unpaired paragraph is not compared; that paragraph has its own entry (N7).

Each of the three (code points, spacing in the paragraph, spacing before it) that applies to a pair is its own entry; a hidden character standing alone between spaces shows as code points and as spacing in the paragraph. For the whole file:
- **Byte-order mark:** one file has it and the other does not.
- **Line ends:** the sets of line-end kinds (CRLF, LF, CR) the two files use differ, or the two texts are equal after the line-end step of 3.2 while the bytes (byte-order mark aside) differ. When the files use the same kinds and their texts differ for other reasons, line ends are not listed separately.
- **Tail:** the two tails differ (blank lines or a final line end after the last paragraph).

So when the command runs and the bytes differ, at least one difference is listed: if the texts after the line-end step are equal, the byte-order mark or line-end rule fires; if they differ, either some opcode is not `equal`, which is itself an entry, or every paragraph pairs and, since equal paragraph words, pieces, whitespace runs, leads (all compared in that case) and tails give equal text, one of those differs and is listed. The exit status is 0 only when the bytes are identical.

### 4.4 Work cap

`difflib` can take time cubic in the list length on repetitive input: on one test machine (2026-11-04), matching 500 copies of one word against 166 repeats of that word twice and another once (498 words) took about 1.5 s, and the same shape at 600 against 600 about 2.5 s. So each matching is capped by the product of the two lists' lengths, counted after the shared start and end are set aside:
- paragraph matching above 250,000 means the comparison cannot run (section 7);
- each later matching (words for a Differs entry, pieces for a Code points entry) may be at most 250,000, and together, in entry order, at most 500,000. A matching that would break either limit is not run, and its entry carries the line `Detail not shown: this tool's matching limit was reached.`
The worst case is then about three capped matchings, about 5 s on that machine.

## 5. Output

### 5.1 Streams and exit status

The report goes to standard output only when the comparison ran. Exit 0: the files are identical, byte for byte. Exit 1: they differ. Exit 2: the comparison could not run, or a usage error (section 7). The whole report is built before any of it is written, so a failure before writing starts leaves no report; the report is written as UTF-8 bytes with LF line ends to the binary standard output, whatever the locale or platform (standard-error lines likewise), with one write call, and if that write fails after part of the report has gone out, that part cannot be taken back; the exit status is still 2. On one Python version, the same two files always give the same report, byte for byte; it carries no date or time, and each path is shown as typed, never resolved.

### 5.2 Layout

Every page starts with the identity line `family-law-toolkit v<version> — not certified for court filing` (pending Q-C5, like the "Educational" line below it), then a blank line. Pages are 60 lines, counting the identity line and the blank line; as in the support report, a form feed takes the place of the line end before each later page's identity line. (The support report's identity line also says it is not affiliated with two support programs; that clause is about support software and is left out here.) Counts use the singular for one (`1 line`, `1 paragraph`, `1 byte`), and a one-line place is written `line 7`, never `lines 7-7`. Only `old:` and `new:` lines, word-difference lines and Notes lines are wrapped: `textwrap.wrap(line, width=78, subsequent_indent=7 spaces, break_long_words=False, break_on_hyphens=False)`, counting code points, so a longer word runs past 78; Notes lines use a 2-space subsequent indent. No other line is wrapped. The body, with invented files:

```text
Comparison of two text files
Educational; not legal advice; not certified for court filing; consult counsel.

Files
  Old (--old): drafts/declaration-v1.txt
    1,204 bytes; 20 lines; 6 paragraphs; byte-order mark: no; line ends: LF
  New (--new): drafts/declaration-v2.txt
    1,265 bytes; 23 lines; 7 paragraphs; byte-order mark: no; line ends: LF

Result: the files differ. Differs 1, only in old 0, only in new 1, spacing 1, code points 0, file 0.

Differences
  1. Differs: old paragraph 3 (lines 7-9), new paragraph 3 (lines 7-9)
     old: Parent B picked up the children at 6:00 p.m. on Fridays.
     new: Parent B picked up the children at 6:30 p.m. on Fridays.
     - old line 8, new line 8: old "6:00", new "6:30", after "the children at"
  2. Only in new: new paragraph 5 (lines 13-15), after old paragraph 4
     new: Parent A and Parent B exchanged the children at the school.
  3. Spacing in the paragraph: old paragraph 6 (lines 17-20), new paragraph 7 (lines 21-23)

Notes
  <the text of N1, then N2 to N7, each wrapped as above>
```

When the bytes are identical, the result line reads `Result: the two files are identical, byte for byte.` and there is no Differences section. The result line, the entry labels and the detail line of 4.4 are pending Q-C5 (the Spacing and Code points labels under Q-C3). Byte counts are file sizes, byte-order mark included, with a comma every three digits, and the report ends with one LF. In the counts, `spacing` counts both spacing labels and `file` counts every File entry. `line ends` reads `LF`, `CRLF`, `CR`, `none` (no line end at all) or `mixed (CRLF 3, LF 28)`, kinds in the order CRLF, LF, CR, leaving out any with no line ends. A run of paragraphs is written as `old paragraphs 3-4 (lines 7-15)`. `byte-order mark` reads `yes` or `no`. Locations in entries (`paragraph N`, `lines X-Y`, `old line 8`, `after old paragraph N`) are pending Q-C2.

### 5.3 Entries

Numbered from 1, in opcode order; a pair's own entries come in the order code points, spacing in the paragraph, spacing before it; file entries come last, in the order byte-order mark, line ends, tail.
- **Differs:** the header; one `old:` line per old paragraph and one `new:` line per new paragraph, each showing its pieces joined by single spaces; then one line per word difference: `old X, new Y`, `only in old X` or `only in new Y`, where each side is its words joined by single spaces inside one pair of quotes, with each paragraph-break token written `(paragraph break)` outside the quotes, in order: `old "a b" (paragraph break) "c"`, `only in new (paragraph break)`, `old "a", new (paragraph break)`. Each word is shown as the piece it came from, in the file's own characters (escaped as below); a piece made only of hidden characters has no word and shows only in `old:`/`new:` lines and Code points entries. A paragraph-break token carries the line number of the first line of the paragraph after it. Each line is led by the line numbers of the side or sides that have words or tokens there (`old line 8, new line 8:`, `new lines 8-9:`) and ends in `after "<context>"`, where the context is up to three words just before the difference in the same file, stopping at a paragraph break, or `at the start of a paragraph` when there are none. The context comes from the new file, except for `only in old`, which uses the old file. When either side of a word difference holds a character outside printable ASCII (U+0020 to U+007E), the line adds, after the context, `; as code points:` and both sides again (paragraph-break tokens kept, context not repeated) with each such character written as `<U+XXXX>`, so look-alike letters can be told apart: `- old line 4, new line 4: old "cafe", new "café", after "met at the"; as code points: old "cafe", new "caf<U+00E9>"`.
- **Only in new:** the header, located in the old file as `after old paragraph N` (the last old paragraph before that place) or `before old paragraph 1`, then one `new:` line per paragraph. **Only in old** is the same with old and new swapped.
- **Spacing:** the header only, labelled `Spacing in the paragraph` or `Spacing before the paragraph`.
- **Code points:** the header, then each differing run of pieces (matched as in 4.2), as `old "agreement<U+200B>", new "agreement"`, with `(nothing)` for an empty side, and every character outside printable ASCII shown as `<U+XXXX>`.
- **File:** `byte-order mark in old only` (or `new only`); `line ends: old <kind>, new <kind>; first different at line N`, with each `<kind>` in the 5.2 form, where line N is the first line whose line end differs or exists in only one file, comparing the Nth line end of each file by position (after an insertion, line N may hold unrelated text in the two files); or `blank lines or line ends after the last paragraph differ`.

Escaping: in every piece, word and path shown, and in every standard-error line, each control character (Cc), hidden character (Cf) and lone surrogate (Cs), each `<` (so that a literal `<U+200B>` in a file cannot pass for an escape), each double quote inside a quoted piece or word, and in paths and standard-error lines each whitespace character other than a space, is written as `<U+XXXX>`, with four to six uppercase hexadecimal digits, as few as the code point needs. So no file, path or argument can start an output line or move the cursor. Right-to-left letters are not escaped and can display reordered.

### 5.4 Notes

Fixed lines, in this order, on every report, each printed under `Notes` indented two spaces, without its N-label. Pending Q-C5 for N1 to N4 and N7, Q-C6 for N5 and Q-C2 for N6; whether to add a line about using the report is pending Q-C7.
- N1: This report lists differences in the text of the two files. It does not say whether any difference matters.
- N2: It reads both files as plain text. Fonts, bold, italics and page layout are not compared, and Markdown markup is read as ordinary characters.
- N3: Moves are not tracked: a paragraph that moved, or the paragraphs it moved past, may be listed as only in old at one place and only in new at another.
- N4: "Old" and "new" are the labels you gave. This tool does not check which file is older, who changed either file, or when.
- N5: This report can repeat text from both files.
- N6: Line numbers count the lines of each file, ended by LF, CR or CRLF, not the lines of a printed or filed page.
- N7: Spacing and code points are not compared inside a Differs entry, and blank lines are not compared at, just before or just after the place of a Differs, Only in old or Only in new entry, except at the end of a file. When both files use the same kinds of line end and their texts differ elsewhere, where the line ends sit is not compared.

## 6. What the tool must never say

These rules, all pending Q-C4, cover all text the tool writes: help, report, notes and error messages. They exclude pieces, words and paths drawn from the files and arguments, the identity line, and the line "Educational; not legal advice; not certified for court filing; consult counsel."
- It never uses any of these words or phrases, as whole words, in any case: significant, insignificant, material, substantive, important, minor, trivial, harmless, prejudicial, favorable, unfavorable, should, must, recommend, advise, final, original, correct, accurate, valid, verified, certified, approved, compliant, conforms, filing-ready, court-ready, redline, blackline, tracked changes, true and correct, conformed, authentic, tampered, altered, forged, evidence, proof, legal.
- It never says the two files' contents are identical, or the same, unless their bytes are. When only spacing, line ends or code points differ, it says the files differ and lists how; it never says "no changes".
- It never names, guesses or implies who made a change, when or why, or that one file came from the other; it never calls a file earlier, later, filed, served, signed or final. `old` and `new` are only the person's labels, so entries say "only in old", "only in new" and "differs", never "added", "removed" or "became".
- It never suggests wording, an edit, or what to do about a difference, and never describes what a difference does.
- It never claims to have compared anything it did not read: formatting, layout, or a PDF or Word file.

## 7. When it cannot run

Every case: exit 2, nothing on standard output (except after a failing write, 5.1), and one line on standard error, `python3 -m family_law_toolkit.compare: error: <message>`. In the messages, `--old` stands for whichever option is at fault and `FILE` for its path as typed, escaped as in 5.3. Usage errors end with `. Run with --help to see what each flag means.`, as in the support command. The whole line is escaped as in 5.3, including any argument the parser repeats. Order: the usage check; rows 2 to 4 for `--old`, then for `--new`; row 5; rows 6 to 8 (the function's content checks) for `--old`, then for `--new`; then the rest. No traceback is ever printed.

| Case | Message (draft) |
|---|---|
| Usage error (3.1) | the argument parser's message, or `--old was given more than once` or `--old cannot be -` |
| Missing, unreadable, or not a regular file | `cannot read --old FILE: <reason>`, where reason is `no such file`, `permission denied`, `it is a folder`, `it is not a regular file` or `it could not be read` |
| Over 200,000 bytes | `--old FILE is larger than 200,000 bytes` |
| Name ends in a refused suffix (3.2) | `--old FILE is not a plain-text file; this version reads plain text and Markdown only` |
| Same file twice | `--old and --new name the same file` |
| NUL byte, or a PDF or zip signature (3.2) | `--old FILE is not a plain-text file; this version reads plain text and Markdown only` |
| Not decodable as UTF-8 | `--old FILE is not UTF-8 text` |
| Empty, only a byte-order mark, or only whitespace | `--old FILE has no text to compare` |
| Over the paragraph cap (4.4) | `too many paragraphs lie between the first and last differences to compare within this tool's limit` |
| Standard output closed, or a write fails | `cannot write output` |
| Any other error | `internal error; the comparison did not finish` |

An error never exits 0 or 1, and only a failing write can leave part of a report on standard output (5.1).

## 8. Decisions, with reasons

- **Paragraph, then word.** Rewrapping a paragraph keeps its words, so it shows as spacing; comparing line by line would show every rewrapped line as differing.
- **Exit 0 only for identical bytes.** "Identical" never means "identical under this tool's rules", and no byte difference can leave the report without at least one entry (4.3). Not every difference is itemised: spacing and code points inside a Differs entry, and where line ends sit when both files use the same kinds and their texts also differ elsewhere (N7).
- **Neutral entry names.** The tool cannot know which file came first, so it says "only in old" and "only in new", not "added" and "removed".
- **No folding of case, quotes or dashes.** They print differently; folding could hide a real edit. Look-alike letters get code points (5.3).
- **Code-point differences listed on their own.** Hidden characters and the same letter in other code points look the same in print.
- **Strict decoding, refusals and caps.** A comparison that would guess at bytes does not run; matching beyond a cap is either refused (paragraphs) or skipped with a line saying so (4.4).

Known limits: a moved paragraph, or the paragraphs it moved past, shows twice; with the same kinds of line end in both files and other differences, a change in where those line ends sit is not listed (N7); invisible characters outside category Cf (such as U+3164 or U+2800) show as visible words, with code points; a long run with many scattered differences can reach the 4.4 cap and lose its word detail; two long files that differ near both ends can be refused under the paragraph cap even when few paragraphs differ; inserting a numbered paragraph shows every later renumbered paragraph as differing; a word hyphenated across a line end is two words; right-to-left letters are not escaped; Unicode data differs between Python versions (4.1).

## 9. Test plan

Invented fixtures only: short texts about Parent A and Parent B, written inside the tests or under `tests/fixtures/compare/`, with no real names, places, case numbers or events. Each row is a test; every row from T2 to T18 also expects exit 1, as do T19's text cases, while T19's argument cases expect exit 2.
- T1 identical bytes: exit 0, the identical result line, no Differences section.
- T2 one word differs: one Differs entry with its line numbers and context.
- T3 a paragraph only in new, first and in the middle; T4 only in old, likewise; T5 two paragraphs against three, showing `(paragraph break)` with its line number: fixtures end alike, and no Spacing or File entry appears in any of them.
- T6 a paragraph rewrapped; T7 tab for spaces, a trailing space, a non-breaking space, U+2000 for U+2002: each one `Spacing in the paragraph` entry. T8 an extra blank line between `equal` paragraphs: one `Spacing before the paragraph` entry.
- T9 a final line end added to a file of several LF-ended lines; T10 CRLF against LF, and two mixed files differing only in line-end order; T11 a byte-order mark in one file: each one File entry. Also: `abc` against `abc` plus LF gives two File entries (line ends: old none, new LF; and the tail); the same mix of kinds in a different order plus a word edit elsewhere gives a Differs entry and no line-ends entry; a paragraph that brings a new kind into a file gives an Only in new entry and a line-ends entry.
- T12 U+200B inside a word; T13 `é` as one code point against `e` plus U+0301: each a Code points entry, not Differs.
- T14 a curly quote for a straight one; T15 a case change; T16 `**Friday**` against `Friday`; T17 Cyrillic `а` for Latin `a`: each Differs, T14 and T17 with code points.
- T18 paragraphs A B C against B C A: one Only in old entry (old paragraph 1, before new paragraph 1) and one Only in new entry (new paragraph 3, after old paragraph 3), no Spacing or File entry.
- T19 escaping and lines: ESC and U+202E inside a word, shown as `<U+XXXX>` in `old:`/`new:` and word lines; a double quote inside a word, shown as `<U+0022>` in word lines and as itself in `old:`/`new:` lines; a literal `<U+200B>`, shown as `<U+003C>U+200B>`; a form feed and U+2028 inside a line, which separate words and do not start a line; a newline in a path (`<U+000A>`), an undecodable byte in a path argument (passed as a missing file where the file system refuses such a name) and a newline and ESC in an unknown option, each escaped on standard error; the report has exactly the expected number of lines.
- T20 no hidden byte difference: from each fixture, 500 seeded random edits (insert, delete or replace one character, drawn from letters, every whitespace character, CR, U+FEFF and Cf characters) that change the bytes and leave a file the command accepts each give exit 1 with at least one entry; the generator is also shown to produce some refused files, which are skipped (positive control).
- T21 every section 7 case (for `--old` and for `--new` where it names one; a folder, `/dev/null` and a FIFO for not a regular file): exit 2, empty standard output, one line; the exact message, except that for usage errors, whose parser text varies between Python versions, only the fixed ending and the escaping are checked; and the check order.
- T22 help: exact bytes and exit 0, even with missing files and unknown options on the same command line.
- T23 closed standard output, a write failing before any byte goes out and one failing after part of the report has gone out, and an error injected mid-comparison: exit 2, one standard-error line, no traceback; empty standard output except in the part-written case.
- T24 never-say: every report from T1 to T20, every section 7 message and the help text hold no section 6 word outside the excluded text. A planted word is caught (positive control). The fixtures hold none of the words (asserted).
- T25 determinism: two runs give the same bytes; a relative path stays relative.
- T26 imports: the package imports only standard-library modules and the toolkit, and none of `socket`, `ssl`, `http`, `urllib`, `ftplib` or `smtplib` (checked from its source, not by running it).
- T27 layout: one golden report, byte for byte, for an invented pair shaped like the 5.2 example, including singular counts and the Notes block; pages of 60 lines with the identity line on each and form feeds between.
- T28 caps: exactly 200,000 bytes runs and 200,001 is refused; a 200,000-byte file of one repeated word against a one-word edit finishes; repetitive lists just over each 4.4 limit (paragraphs, one matching, the shared total) give exit 2 or the detail line, and each run finishes in under 10 s.

The suite runs on Python 3.9 and the latest 3.x, and the command is also run by hand with hostile arguments (a newline in a path, an unknown option, a closed standard output).

## 10. Phases

Pending Q-C11.
1. This spec: plain text and Markdown, sections 2 to 9. Building it also updates AGENTS.md's Status section, the README and the CHANGELOG, and that wording is reviewed before release.
2. Margin line numbers and page-and-line locations, only after Q-C2 is answered.
3. DOCX, read with `zipfile` and `xml` from the standard library with entity expansion refused, only after Q-C8 is answered.
4. PDF, only after Q-C9 is answered and a decision on reading it: the standard library cannot read text from a PDF.

## 11. Questions for the GC

These are questions only; where a line is offered, it is put up to accept, reject or reword.
- **Q-C1. Which papers.** Which kinds of family-law papers would a person compare with this tool, and is there any kind it should not be offered for, or should warn about (for example, a paper already filed, or a Judicial Council form)? Does "comparing drafts", the README's name for it, say anything about those papers that it should not?
- **Q-C2. Line numbers and locations.** Text copied from line-numbered pleading paper can carry the margin numbers. Should a later phase keep them as text, remove them, or use them as locations? Could "paragraph N, lines X-Y" of the saved file mislead a person, for example by being read as a page and line of a filed paper, or "paragraph N" as the paper's own numbered paragraph? Accept, reject or reword N6.
- **Q-C3. Spacing and code points.** Is there any paper in which spacing, line breaks, blank lines, a hidden character, or a letter written with other code points carries a meaning that the labels "Spacing" and "Code points" would understate? Accept, reject or reword those labels.
- **Q-C4. Words to avoid.** Accept, reject or extend the section 6 rules and word list. Are there words with a court meaning the tool must avoid, or words on the list it may use?
- **Q-C5. Fixed lines.** Accept, reject or reword N1 to N4 and N7, the identity line on each page, the result lines, the entry labels ("Differs", "Only in old", "Only in new", and "File" with its three texts in 5.3), the detail line of 4.4, the toolkit's existing line "Educational; not legal advice; not certified for court filing; consult counsel." as used on this tool, the help text's first line "Compare the text of two versions of a document", and its sentences "It lists differences in the text. It does not say whether any difference matters."
- **Q-C6. Private text.** Accept, reject or reword N5. Is there anything else the tool must say or do because its report reprints the text of both files and their paths as typed?
- **Q-C7. Using the report.** A person may compare a paper they drafted with one they later received, served or filed. Should the help or the report say anything about showing the report to a court or the other party, beyond N4?
- **Q-C8. Word files.** For a later DOCX phase, what text is the document: with tracked changes accepted, rejected, or both shown? Are comments, headers, footers and footnotes part of it?
- **Q-C9. PDF files.** For a later PDF phase, filed copies can carry court stamps, headers and footers on each page. Should a comparison include them, and does comparing a filed copy raise anything a stranger must be told?
- **Q-C10. Requirements from today's practice.** Is there a requirement from the way you compare drafts today that this spec does not meet? Please state it as a requirement, with invented inputs.
- **Q-C11. Scope and order.** Do the phase 1 scope and non-goals (section 2) match what you want for this tool, and may phase 1 be built before Q-C2, Q-C8 and Q-C9 are answered?
