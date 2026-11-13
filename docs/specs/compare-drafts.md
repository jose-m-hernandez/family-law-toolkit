# Compare drafts: behaviour spec

Status: DRAFT. Not accepted, and nothing is built. This tool's legal reviewer, the General Counsel (GC), answered Q-C1 to Q-C11 on 2026-11-11 (`2026-11-04-gc-reply-flt-compare-drafts.md`) and Q-C12 the same day (the Status Log of `2026-11-11-cto-questions-for-gc-flt-compare-drafts-q-c12.md`) and Q-C13 the same day (the Status Log of `2026-11-11-cto-questions-for-gc-flt-compare-drafts-q-c13.md`); section 11 holds no open question.
Date: 2026-11-11.
Revision: draft 14.

Written from requirements only: what a person preparing California family-law paperwork needs when comparing the text of two files. "Compare drafts" is only this feature's internal name; the README and the help say "compare two files' text", because one file may be a served or filed copy (Q-C1). Every example and test fixture is invented.

## 1. Purpose

Show a person, in plain text, the differences section 4 defines between the text of two files, so they can read each difference for themselves. Typical uses (Q-C1): a person's own draft against a later draft (a declaration, a proposed order, a stipulation, a letter), or a draft against the copy that was later served or received, after the person saved both as text. The tool never judges a difference or says what to do about one.

## 2. Scope and non-goals

The GC accepted this section as phase 1's scope (Q-C11), and phase 1 may be built before the later phases of section 10 are settled.

In (phase 1):
- exactly two files, named with `--old` and `--new`, each UTF-8 plain text; Markdown is read as plain text (3.3);
- a comparison by paragraph, then by word, with differences in spacing, line ends, the byte-order mark and hidden or look-alike characters listed separately (section 4);
- a plain-text report on standard output that names each file's path, byte size and sha256, and an exit status (section 5).

Out:
- judging a difference: whether it matters, what it means or does, or which version is better;
- suggesting, rewriting, merging or accepting text; writing or changing any file;
- who changed a file, when, or which file is older or came from the other (`old` and `new` are the person's labels);
- formatting: fonts, bold, italics, page layout, headers and footers, rendered Markdown;
- PDF and DOCX (later phases, section 10); RTF, ODT and images, until a person asks for them (Q-C11);
- treating margin line numbers as anything but text (a later phase, section 10), and locations given as a page and line, which this tool cannot know (Q-C2);
- tracking moved text: matching keeps the longest run of paragraphs in order, so a moved paragraph, or the paragraphs it moved past, may be listed as only in old at one place and only in new at another;
- more than two files, folders, standard input, the network, and any temporary or log file.

## 3. Inputs

The command is `python3 -m family_law_toolkit.compare --old FILE --new FILE` (a working name, settled at release). It needs Python 3.9 or later and the standard library only (for example `argparse`, `difflib`, `hashlib`, `os`, `sys`, `textwrap` and `unicodedata`), like the rest of the repository. A Python API mirrors the support tool's `compute()` and `render_report()`, with working names: `check(data)` runs the content checks of section 7 (rows 6 to 8) on one file's bytes; `compare(old, new)` compares two byte strings that `check()` has accepted and returns a result; `render_report(result, old_path, new_path)` renders it, with the two paths as typed. The command runs the other checks and calls `check()` once per file, in the order section 7 gives.

### 3.1 Options

| Option | Meaning |
|---|---|
| `--old FILE` | One file. Required, given exactly once. |
| `--new FILE` | The other file. Required, given exactly once. |
| `-h`, `--help` | Write the help text (3.4), then one LF, to standard output and exit 0. Reads no file, and wins over every other argument, as in the support command. |

A missing, repeated, unknown or abbreviated option, any other argument, or a `FILE` of `-` is a usage error (section 7). A path that starts with `-` is given as `--old=-notes.txt` or `./-notes.txt`. A repeated option and a `FILE` of `-` each need their own check, because the argument parser keeps the last value of a repeated option and accepts `-` as a value.

### 3.2 Files

- Each path is checked with `os.stat` before it is opened, and must be a regular file, so a folder, device or FIFO is refused without being opened. At most 200,001 bytes are read, and a file may be at most 200,000 bytes; matching work is also capped (4.4).
- A leading UTF-8 byte-order mark is removed and recorded. The rest must be valid UTF-8, decoded strictly. Reason: replacing a bad byte could make two different files read alike and hide a difference.
- The checks in this section run in section 7's table order. A file is refused as not plain text if it holds a NUL byte, if its bytes after any byte-order mark start with `%PDF-` or with the zip signature `PK\x03\x04` (a DOCX file is a zip), or if its name ends in `.pdf`, `.docx`, `.doc`, `.rtf` or `.odt`, in any case. Reason: phase 1 must not compare the bytes of a binary file as if they were words.
- Line ends: each CRLF, then each remaining lone CR, becomes LF, and each file's line ends are recorded by kind, in order. After that, only LF ends a line: a form feed, vertical tab, U+0085, U+2028 or U+2029 inside a line is whitespace, not a line end. Lines are numbered from 1, and a final line end does not start a new line.
- A file that is empty, holds only a byte-order mark, or holds nothing but whitespace (4.1) has no text to compare. `--old` and `--new` naming the same file (`os.path.samefile`) is refused.

### 3.3 Markdown

Read as plain text (N2 says so). `#`, `*`, `_`, backticks and link syntax are ordinary characters, so `**Friday**` against `Friday` is a wording difference.

### 3.4 Help text

The first line, the "Educational" line, the two sentences after the file limits (Q-C5) and the sentence after them (Q-C7) are as the GC accepted or worded them. Those three sentences are the help sentences of section 6: fixed lines, outside its list, though the Q-C7 sentence uses a listed word (Q-C12). "One file" and "The other file" follow Q-C5's reason (no "version", which implies one file came from the other). The rest is reviewed before release.

```text
usage: python3 -m family_law_toolkit.compare --old FILE --new FILE

Compare the text of two files.
Educational; not legal advice; not certified for court filing; consult counsel.

Required:
  --old FILE
      One file: plain text or Markdown
  --new FILE
      The other file: plain text or Markdown

Each file is read as UTF-8 text, up to 200,000 bytes. PDF and Word files are
not read. "Old" and "new" are your labels; this tool does not check which file
is older.
It lists differences in the text. It does not say whether any difference
matters.
The report is not a certified comparison and is not a court record.

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

Short tokens (Q-C10, requirement 2): a differing figure (`$1,200.00` / `$1,250.00`), date (`March 3` / `March 8`), negation (`shall pay` / `shall not pay`, which gives an only-in-new `not`) or checkbox written as text (`[X]` / `[ ]`) changes its paragraph's words, so that paragraph pair is never `equal` and never reaches 4.3's Spacing or Hidden or look-alike characters entries. Inside its Differs entry the token is its own word difference showing both sides (5.3), however long the paragraph: the shared start and end of the word lists are set aside first, so a lone token is matched alone. Differing words next to each other fall in one opcode and share one line that shows both sides (`old "3/3 $1,200", new "3/8 $1,250"`); the GC ruled that this meets Q-C10 (Q-C12). A lone token's matching is at most one word against one, so a long paragraph alone never reaches the 4.4 limit; the limit is reached when an entry's first and last word differences lie far apart (lists, after the shared start and end, whose lengths multiply to more than 250,000, about 500 words each), or once earlier entries have used up the shared total, and the entry then carries the 4.4 detail line for a Differs entry (Line A), which says that the words, figures and dates that differ inside it are not listed (Q-C12, Q-C13).

### 4.3 Differences other than wording

The labels below are the GC's (Q-C3). For each `equal` pair:
- **Hidden or look-alike characters** differ when the two paragraphs' pieces differ: the words match, but a hidden character, or the same letter written with different code points, differs.
- **Spacing** differs in the paragraph when the two paragraphs' whitespace runs differ, and before it when the two leads differ and the paragraphs before them are themselves an `equal` pair (or both paragraphs are first in their files). A lead next to an unpaired paragraph is not compared; that paragraph has its own entry (N7).

Each of the three (hidden or look-alike characters, spacing in the paragraph, spacing before it) that applies to a pair is its own entry; a hidden character standing alone between spaces shows as both a hidden or look-alike characters entry and spacing in the paragraph. For the whole file:
- **Byte-order mark:** one file has it and the other does not.
- **Line ends:** the sets of line-end kinds (CRLF, LF, CR) the two files use differ, or the two texts are equal after the line-end step of 3.2 while the bytes (byte-order mark aside) differ. When the files use the same kinds and their texts differ for other reasons, line ends are not listed separately.
- **Tail:** the two tails differ (blank lines or a final line end after the last paragraph).

So when the command runs and the bytes differ, at least one difference is listed: if the texts after the line-end step are equal, the byte-order mark or line-end rule fires; if they differ, either some opcode is not `equal`, which is itself an entry, or every paragraph pairs and, since equal paragraph words, pieces, whitespace runs, leads (all compared in that case) and tails give equal text, one of those differs and is listed. The exit status is 0 only when the bytes are identical.

### 4.4 Work cap

`difflib` can take time cubic in the list length on repetitive input: on one test machine (2026-11-04), matching 500 copies of one word against 166 repeats of that word twice and another once (498 words) took about 1.5 s, and the same shape at 600 against 600 about 2.5 s. So each matching is capped by the product of the two lists' lengths, counted after the shared start and end are set aside:
- paragraph matching above 250,000 means the comparison cannot run (section 7);
- each later matching (words for a Differs entry, pieces for a Hidden or look-alike characters entry) may be at most 250,000, and together, in entry order, at most 500,000; a matching that is not run adds nothing to the total. A matching that would break either limit is not run, and its entry carries, in place of its word differences (Differs) or its runs of pieces (Hidden or look-alike characters), a detail line. The entry kind selects the line, and each is one fixed line with no plural logic, true for one paragraph or a run (Q-C5, Q-C12, Q-C13):
  - Line A, for a Differs entry: `Detail not shown: this tool's matching limit was reached. The files differ in the paragraphs this entry names; words, figures and dates that differ inside them are not listed.`
  - Line B, for a Hidden or look-alike characters entry: `Detail not shown: this tool's matching limit was reached. The files differ in the paragraphs this entry names; hidden or look-alike characters that differ inside them are not listed.`
  The entry keeps its header with both file locations (and a Differs entry its `old:`/`new:` lines), and the result line counts it like any other entry (Q-C12). A Hidden or look-alike characters entry can reach the limit: its two paragraphs' words are equal, and their pieces (4.1) differ at both ends of a long paragraph (T35).
The worst case is then about three capped matchings, about 5 s on that machine.

## 5. Output

### 5.1 Streams and exit status

The report goes only to standard output, and errors only to standard error (Q-C6); nothing else is written anywhere. The report goes out only when the comparison ran. Exit 0: the files are identical, byte for byte. Exit 1: they differ. Exit 2: the comparison could not run, or a usage error (section 7). The whole report is built before any of it is written, so a failure before writing starts leaves no report; the report is written as UTF-8 bytes with LF line ends to the binary standard output, whatever the locale or platform (standard-error lines likewise), with one write call, and if that write fails after part of the report has gone out, that part cannot be taken back; the exit status is still 2. On one Python version, the same two files always give the same report, byte for byte; it carries no date or time, and each path is shown as typed, never resolved.

### 5.2 Layout

Every page starts with the identity line `family-law-toolkit v<version> — not certified for court filing` (accepted under Q-C5, like the "Educational" line below it), then a blank line. Pages are 60 lines, counting the identity line and the blank line; as in the support report, a form feed takes the place of the line end before each later page's identity line. (The support report's identity line also says it is not affiliated with two support programs; that clause is about support software and is left out here.) Counts use the singular for one (`1 line`, `1 paragraph`, `1 byte`), and a one-line place is written `file line 7`, never `file lines 7-7`. Only `old:` and `new:` lines, word-difference lines, runs of pieces (5.3), the detail line (4.4) and Notes lines are wrapped: `textwrap.wrap(line, width=78, subsequent_indent=7 spaces, break_long_words=False, break_on_hyphens=False)`, counting code points, so a longer word runs past 78; Notes lines use a 2-space subsequent indent. No other line is wrapped. An entry's first line is two spaces, its number, `. `, its label, and for a paragraph entry `: ` and its locations (a File entry's text follows `File: `); the lines under it are indented five spaces, with word-difference lines and runs of pieces led by `- `. The detail line (4.4: Line A for a Differs entry, Line B for a Hidden or look-alike characters entry) stands where the word-difference lines (Differs) or the runs of pieces (Hidden or look-alike characters) would be, after any `old:`/`new:` lines, indented five spaces, not led by `- `, and wrapped as above. The other indents are as the example shows, fixed by the golden report (T27). The body, with invented files:

```text
Comparison of two text files
Educational; not legal advice; not certified for court filing; consult counsel.

Files
  Old (--old): drafts/declaration-v1.txt
    1,204 bytes; 20 lines; 6 paragraphs; byte-order mark: no; line ends: LF
    sha256: <64 lowercase hexadecimal digits>
  New (--new): drafts/declaration-v2.txt
    1,265 bytes; 23 lines; 7 paragraphs; byte-order mark: no; line ends: LF
    sha256: <64 lowercase hexadecimal digits>

Result: the files differ. Differs 1, only in old 0, only in new 1, spacing 1, hidden or look-alike characters 0, file 0.

Differences
  1. Differs: old file paragraph 3, file lines 7-9; new file paragraph 3, file lines 7-9
     old: Parent B picked up the children at 1:20 p.m. on Fridays.
     new: Parent B picked up the children at 1:50 p.m. on Fridays.
     - old file line 8, new file line 8: old "1:20", new "1:50", after "the children at"
  2. Only in new: new file paragraph 5, file lines 13-15; after old file paragraph 4
     new: Parent A and Parent B exchanged the children at the school.
  3. Spacing in the paragraph: old file paragraph 6, file lines 17-20; new file paragraph 7, file lines 21-23

Notes
  <the text of N1, then N2 to N8, each wrapped as above>
```

The header ties the report to the exact bytes read (Q-C10, requirement 1; Q-C7): each file's path as typed (escaped as in 5.3), its byte size, and on its own line the sha256 (`hashlib.sha256`) of all of those bytes, byte-order mark included, as 64 lowercase hexadecimal digits. When the bytes are identical, the result line reads `Result: the two files are identical, byte for byte.` and there is no Differences section. The GC accepted the result lines and the entry labels (Q-C5) and reworded the Hidden or look-alike characters label (Q-C3), the detail lines of 4.4 (Q-C5, Q-C12, then Q-C13) and, to follow that label, the result line's count name `hidden or look-alike characters` (Q-C12). Byte counts are file sizes, byte-order mark included, with a comma every three digits, and the report ends with one LF. In the counts, `spacing` counts both spacing labels and `file` counts every File entry. `line ends` reads `LF`, `CRLF`, `CR`, `none` (no line end at all) or `mixed (CRLF 3, LF 28)`, kinds in the order CRLF, LF, CR, leaving out any with no line ends. A run of paragraphs is written as `old file paragraphs 3-4, file lines 7-15`. `byte-order mark` reads `yes` or `no`. Every location in an entry is labelled as the file's own (Q-C2): `file paragraph N`, `file paragraphs N-M`, `file lines X-Y`, `file line X`, `old file line 8`, `after old file paragraph N`, never a bare `paragraph` or `line`; an entry header gives one side as `<side> file paragraph N, file lines X-Y`, and two sides joined by `; `.

### 5.3 Entries

Numbered from 1, in opcode order; a pair's own entries come in the order hidden or look-alike characters, spacing in the paragraph, spacing before it; file entries come last, in the order byte-order mark, line ends, tail.
- **Differs:** the header; one `old:` line per old paragraph and one `new:` line per new paragraph, each showing its pieces joined by single spaces; then one line per word difference: `old X, new Y`, `only in old X` or `only in new Y`, where each side is its words joined by single spaces inside one pair of quotes, with each paragraph-break token written `(paragraph break)` outside the quotes, in order: `old "a b" (paragraph break) "c"`, `only in new (paragraph break)`, `old "a", new (paragraph break)`. Each word is shown as the piece it came from, in the file's own characters (escaped as below); a piece made only of hidden characters has no word and shows only in `old:`/`new:` lines and Hidden or look-alike characters entries. A paragraph-break token carries the line number of the first line of the paragraph after it. Each line is led by the line numbers of the side or sides that have words or tokens there (`old file line 8, new file line 8:`, `new file lines 8-9:`) and ends in `after "<context>"`, where the context is up to three words just before the difference in the same file, stopping at a paragraph break, or `at the start of a paragraph` when there are none. The context comes from the new file, except for `only in old`, which uses the old file. When either side of a word difference holds a character outside printable ASCII (U+0020 to U+007E), the line adds, after the context, `; as code points:` and both sides again (paragraph-break tokens kept, context not repeated) with each such character written as `<U+XXXX>`, so look-alike letters can be told apart: `- old file line 4, new file line 4: old "cafe", new "café", after "met at the"; as code points: old "cafe", new "caf<U+00E9>"`. The four short-token kinds of 4.2 give lines such as (leading line numbers left out): `old "$1,200.00", new "$1,250.00", after "the sum of"`, `old "3", new "8", after "due on March"`, `only in new "not", after "that Respondent shall"`, `old "[X]", new "[ ]", at the start of a paragraph`.
- **Only in new:** the header, located in the old file by `; after old file paragraph N` (the last old paragraph before that place) or `; before old file paragraph 1`, then one `new:` line per paragraph. **Only in old** is the same with old and new swapped.
- **Spacing:** the header only, labelled `Spacing in the paragraph` or `Spacing before the paragraph`.
- **Hidden or look-alike characters:** the header, then each differing run of pieces (matched as in 4.2), as `old "agreement<U+200B>", new "agreement"`, with `(nothing)` for an empty side, and every character outside printable ASCII shown as `<U+XXXX>`, so each entry still names the code points (Q-C3).
- **File:** `byte-order mark in old only` (or `new only`); `line ends: old <kind>, new <kind>; first different at file line N`, with each `<kind>` in the 5.2 form, where line N is the first line whose line end differs or exists in only one file, comparing the Nth line end of each file by position (after an insertion, line N may hold unrelated text in the two files); or `blank lines or line ends after the last paragraph differ`.

Escaping: in every piece, word and path shown, and in every standard-error line, each control character (Cc), hidden character (Cf) and lone surrogate (Cs), each `<` (so that a literal `<U+200B>` in a file cannot pass for an escape), each double quote inside a quoted piece or word, and in paths and standard-error lines each whitespace character other than a space, is written as `<U+XXXX>`, with four to six uppercase hexadecimal digits, as few as the code point needs. So no file, path or argument can start an output line or move the cursor. Right-to-left letters are not escaped and can display reordered.

### 5.4 Notes

Fixed lines, in this order, on every report, each printed under `Notes` indented two spaces, without its N-label. All are as the GC accepted or worded them (N1 to N4 and N7 under Q-C5, with N7's first sentence as she amended it under Q-C12, N5 Q-C6, N6 Q-C2, N8 Q-C1); the GC added no report line about using the report (Q-C7). N4 and N6, like the Q-C7 help sentence, contain section 6 words; as fixed lines they are outside its list (Q-C12).
- N1: This report lists differences in the text of the two files. It does not say whether any difference matters.
- N2: It reads both files as plain text. Fonts, bold, italics, page layout, checked boxes and form fields are not compared, and Markdown markup is read as ordinary characters.
- N3: Moves are not tracked: a paragraph that moved, or the paragraphs it moved past, may be listed as only in old at one place and only in new at another.
- N4: "Old" and "new" are the labels you gave. This tool does not check which file is older, who changed either file, when, or whether either was filed or served.
- N5: This report can repeat text from both files and prints their paths as you typed them. Keep it as private as the files.
- N6: Paragraph and line numbers in this report count the paragraphs and lines of each file as saved (lines end at LF, CR or CRLF). They are not the paper's own numbered paragraphs, or the page and line numbers of a printed or filed copy.
- N7: Spacing and hidden or look-alike characters are not compared inside a Differs entry. Blank lines are not compared at, just before or just after a Differs, Only in old or Only in new entry, except at the end of a file. When both files use the same kinds of line end and their text differs elsewhere, where the line ends sit is not compared.
- N8: If a file was made from a PDF or a form, checked boxes, form fields, stamps and signatures may be missing from it. This report covers only the text in the two files.

## 6. What the tool must never say

The GC accepted these rules and the list, and extended the list (Q-C4). The rules cover all text the tool writes: help, report, notes and error messages. The list (the first rule below) is ruled under Q-C12: the list governs the text the tool generates about the two files (entries, result and count lines, error messages). The fixed lines named in the spec are outside it: N1 to N8, the help sentences, the identity line, the "Educational" line and the two detail lines of 4.4 (Line A and Line B, named by Q-C13). The help sentences are those 3.4 names, and the "Educational" line reads "Educational; not legal advice; not certified for court filing; consult counsel." The GC's reason: "Each of them denies or limits the very thing its listed word names." The fixed lines that use listed words are N4 (`changed`, `filed`, `served`), N6 (`filed`), the Q-C7 help sentence (`certified`), the identity line (`certified`) and the "Educational" line (`certified`, `legal`). Within generated text, the list governs only the tool's own words, never text quoted from either file: pieces, words, hashes and paths drawn from the files and arguments are excluded (Q-C4). The tool needs no listed word in generated text, so error messages are written without them (`cannot be read as UTF-8`, not `not valid UTF-8`); the help's other lines hold none either. T24 checks generated text against the list and checks the fixed lines byte for byte against the spec (Q-C12).
- It never uses any of these words or phrases, as whole words, in any case: significant, insignificant, material, substantive, important, minor, trivial, harmless, prejudicial, favorable, unfavorable, should, must, recommend, advise, final, original, correct, accurate, valid, verified, certified, approved, compliant, conforms, filing-ready, court-ready, redline, blackline, tracked changes, true and correct, conformed, authentic, tampered, altered, forged, evidence, proof, legal; changed, edited, revised, modified, inserted, deleted, struck, amended, supersedes, superseded, operative; filed, served, signed, executed, endorsed, stamped, stipulated, agreed; unchanged, matches, no changes.
- It never says the two files' contents are identical, or the same, unless their bytes are. When only spacing, line ends or code points differ, it says the files differ and lists how; it never says "no changes".
- It never names, guesses or implies who made a change, when or why, or that one file came from the other; it never calls a file earlier, later, filed, served, signed or final. `old` and `new` are only the person's labels, so entries say "only in old", "only in new" and "differs", never "added", "removed" or "became".
- It never suggests wording, an edit, or what to do about a difference, and never describes what a difference does.
- It never claims to have compared anything it did not read: formatting, layout, or a PDF or Word file.

## 7. When it cannot run

Every case: exit 2, nothing on standard output (except after a failing write, 5.1), and one line on standard error, `python3 -m family_law_toolkit.compare: error: <message>`. In the messages, `--old` stands for whichever option is at fault and `FILE` for its path as typed, escaped as in 5.3. Usage errors end with `. Run with --help to see what each flag means.`, as in the support command. The whole line is escaped as in 5.3, including any argument the parser repeats. Order: the usage check (below); rows 2 to 4 for `--old`, then for `--new`; row 5; rows 6 to 8 (the function's content checks) for `--old`, then for `--new`; then the rest. No traceback is ever printed.

| Case | Message (draft) |
|---|---|
| Usage error (3.1) | the argument parser's message, or `--old was given more than once` or `--old cannot be -` |
| Missing, unreadable, or not a regular file | `cannot read --old FILE: <reason>`, where reason is `no such file`, `permission denied`, `it is a folder`, `it is not a regular file` or `it could not be read` |
| Over 200,000 bytes | `--old FILE is larger than 200,000 bytes` |
| Name ends in a refused suffix (3.2) | `--old FILE is not a plain-text file; this version reads plain text and Markdown only` |
| Same file twice | `--old and --new name the same file` |
| NUL byte, or a PDF or zip signature (3.2) | `--old FILE is not a plain-text file; this version reads plain text and Markdown only` |
| Not decodable as UTF-8 | `--old FILE cannot be read as UTF-8` |
| Empty, only a byte-order mark, or only whitespace | `--old FILE has no text to compare` |
| Over the paragraph cap (4.4) | `too many paragraphs lie between the first and last differences to compare within this tool's limit` |
| Standard output closed, or a write fails | `cannot write output` |
| Any other error | `internal error; the comparison did not finish` |

The usage check runs in this order (as built, where the first draft was silent): the argument parser's own errors (a missing, unknown or abbreviated option, or any other argument); then, for `--old` and then for `--new`, `was given more than once` before `cannot be -`.

The reason in row 2 comes from the error number of the failed `os.stat` or `open` (as built): no such file or not a directory give `no such file`; permission denied or operation not permitted give `permission denied`; any other error gives `it could not be read` (for example an input/output error). A folder and a file that is not regular are told apart by the file mode, before the file is opened.

An error never exits 0 or 1, and only a failing write can leave part of a report on standard output (5.1).

## 8. Decisions, with reasons

- **Paragraph, then word.** Rewrapping a paragraph keeps its words, so it shows as spacing; comparing line by line would show every rewrapped line as differing.
- **Exit 0 only for identical bytes.** "Identical" never means "identical under this tool's rules", and no byte difference can leave the report without at least one entry (4.3). Not every difference is itemised: spacing and hidden or look-alike characters inside a Differs entry, the word differences of a Differs entry and the hidden or look-alike characters of a Hidden or look-alike characters entry past the 4.4 limit (its detail line says so), and where line ends sit when both files use the same kinds and their texts also differ elsewhere (N7).
- **Neutral entry names.** The tool cannot know which file came first, so it says "only in old" and "only in new", not "added" and "removed".
- **No folding of case, quotes or dashes.** They print differently; folding could hide a real edit. Look-alike letters get code points (5.3).
- **Hidden or look-alike characters listed on their own.** Hidden characters and the same letter in other code points look the same in print, and can make a name, a case number, an amount or a date look the same while the text differs (Q-C3). A visibly differing short token is a word difference instead (4.2).
- **The header carries hashes.** Each file's sha256 lets anyone shown the report check it against the files (Q-C7, Q-C10).
- **Strict decoding, refusals and caps.** A comparison that would guess at bytes does not run; matching beyond a cap is either refused (paragraphs) or skipped with the detail line, which says what is not listed (4.4).

Known limits: a moved paragraph, or the paragraphs it moved past, shows twice; with the same kinds of line end in both files and other differences, a change in where those line ends sit is not listed (N7); invisible characters outside category Cf (such as U+3164 or U+2800) show as visible words, with code points; an entry whose first and last word differences lie far apart, or any entry after earlier entries have used up the shared total, can reach the 4.4 limit and lose its word detail, short tokens included, and its detail line then says so (Q-C12); differing words next to each other share one word-difference line, which shows both sides (Q-C12); two long files that differ near both ends can be refused under the paragraph cap even when few paragraphs differ; inserting a numbered paragraph shows every later renumbered paragraph as differing; a word hyphenated across a line end is two words; right-to-left letters are not escaped; Unicode data differs between Python versions (4.1).

## 9. Test plan

Invented fixtures only: short texts about Parent A and Parent B, written inside the tests or under `tests/fixtures/compare/`, with no real names, places, case numbers or events. Each row is a test; every row from T2 to T18 and from T29 to T35 also expects exit 1, as do T19's text cases, while T19's argument cases expect exit 2.
- T1 identical bytes: exit 0, the identical result line, no Differences section.
- T2 one word differs: one Differs entry with its line numbers and context.
- T3 a paragraph only in new, first and in the middle; T4 only in old, likewise; T5 two paragraphs against three, showing `(paragraph break)` with its line number: fixtures end alike, and no Spacing or File entry appears in any of them.
- T6 a paragraph rewrapped; T7 tab for spaces, a trailing space, a non-breaking space, U+2000 for U+2002: each one `Spacing in the paragraph` entry. T8 an extra blank line between `equal` paragraphs: one `Spacing before the paragraph` entry.
- T9 a final line end added to a file of several LF-ended lines; T10 CRLF against LF, and two mixed files differing only in line-end order; T11 a byte-order mark in one file: each one File entry. Also: `abc` against `abc` plus LF gives two File entries (line ends: old none, new LF; and the tail); the same mix of kinds in a different order plus a word edit elsewhere gives a Differs entry and no line-ends entry; a paragraph that brings a new kind into a file gives an Only in new entry and a line-ends entry.
- T12 U+200B inside a word; T13 `é` as one code point against `e` plus U+0301: each a Hidden or look-alike characters entry, not Differs.
- T14 a curly quote for a straight one; T15 a case change; T16 `**Friday**` against `Friday`; T17 Cyrillic `а` for Latin `a`: each Differs, T14 and T17 with code points.
- T18 paragraphs A B C against B C A: one Only in old entry (old file paragraph 1, before new file paragraph 1) and one Only in new entry (new file paragraph 3, after old file paragraph 3), no Spacing or File entry.
- T19 escaping and lines: ESC and U+202E inside a word, shown as `<U+XXXX>` in `old:`/`new:` and word lines; a double quote inside a word, shown as `<U+0022>` in word lines and as itself in `old:`/`new:` lines; a literal `<U+200B>`, shown as `<U+003C>U+200B>`; a form feed and U+2028 inside a line, which separate words and do not start a line; a newline in a path (`<U+000A>`), an undecodable byte in a path argument (passed as a missing file where the file system refuses such a name) and a newline and ESC in an unknown option, each escaped on standard error; the report has exactly the expected number of lines.
- T20 no hidden byte difference: from each fixture, 500 seeded random edits (insert, delete or replace one character, drawn from letters, every whitespace character, CR, U+FEFF and Cf characters) that change the bytes and leave a file the command accepts each give exit 1 with at least one entry; the generator is also shown to produce some refused files, which are skipped (positive control).
- T21 every section 7 case (for `--old` and for `--new` where it names one; a folder, `/dev/null` and a FIFO for not a regular file): exit 2, empty standard output, one line; the exact message, except that for usage errors, whose parser text varies between Python versions, only the fixed ending and the escaping are checked; and the check order.
- T22 help: exact bytes and exit 0, even with missing files and unknown options on the same command line.
- T23 closed standard output, a write failing before any byte goes out and one failing after part of the report has gone out, and an error injected mid-comparison: exit 2, one standard-error line, no traceback; empty standard output except in the part-written case.
- T24 never-say (Q-C12): no section 6 word, as a whole word in any case, in the generated text: every line other than the fixed lines of every report from T1 to T19, from T20's fixtures before their edits, and from T29 to T34, and every section 7 message; nor in the help's lines other than the help sentences and the "Educational" line. The fixtures and paths hold none of the words (asserted), so a hit can only be the tool's own text. The fixed lines are checked byte for byte against this spec: the identity line on every page, the "Educational" line, Line A and Line B of 4.4 (Q-C13), the Notes block (N1 to N8, each wrapped as 5.2 says) and the help text (3.4, as in T22). Positive controls: a listed word planted in generated text is caught, and so is a one-character change to a fixed line.
- T25 determinism: two runs give the same bytes; a relative path stays relative.
- T26 imports: the package imports only standard-library modules and the toolkit, and none of `socket`, `ssl`, `http`, `urllib`, `ftplib` or `smtplib` (checked from its source, not by running it).
- T27 layout: one golden report, byte for byte, for an invented pair shaped like the 5.2 example, including both sha256 lines, the `file paragraph` / `file lines` location wording, a one-line `file line` place, the result line with its `hidden or look-alike characters` count, a Hidden or look-alike characters entry, a Differs entry carrying Line A, and the Notes block N1 to N8 with N7 as amended (Q-C12); pages of 60 lines with the identity line on each and form feeds between.
- T28 caps: exactly 200,000 bytes runs and 200,001 is refused; a 200,000-byte file of one repeated word against a one-word edit finishes; repetitive lists just over each 4.4 limit (paragraphs, one matching, the shared total) give exit 2 (paragraphs) or the detail line (one matching, the shared total), and each run finishes in under 10 s.
- T29 to T32 short tokens (Q-C10, requirement 2), each one differing token inside a paragraph of at least 300 words (T32 at its start, the others in its middle), files otherwise byte-identical: exactly one Differs entry holding exactly one word-difference line, with the 5.3 example ending, and no Spacing, Hidden or look-alike characters or File entry. T29 a figure, `$1,200.00` against `$1,250.00`; T30 a date, `March 3` against `March 8` (`old "3", new "8"`); T31 a negation, `shall pay` against `shall not pay` (`only in new "not"`); T32 a checkbox written as text, `[X]` against `[ ]` (`at the start of a paragraph`). Each also on a second pair that adds, elsewhere in the same paragraph, a tab for a space and a U+200B inside a word: the same single word-difference line, and still no Spacing or Hidden or look-alike characters entry.
- T33 header (Q-C10, requirement 1): for `--old ./a.txt --new b/c.txt` with a byte-order mark in one file, each path as typed, the byte size, and a sha256 line equal to `hashlib.sha256` of the file's bytes, byte-order mark included; replacing one ASCII letter of one file with another changes only that file's sha256 line. Singular counts: a file holding only `a` shows `1 byte; 1 line; 1 paragraph`.
- T34 matching limit (Q-C12), the GC's invented test of a paragraph over the limit whose only difference is a figure, reached through the shared total because a lone token's own matching is one word against one (4.2): two files of five one-line paragraphs separated by blank lines, the second paragraph byte-identical in the two files and so the fourth; the first is 500 copies of `a` against 500 of `b`, the third 500 of `c` against 500 of `d` (each matching 500 × 500 = 250,000, together 500,000, both run); the fifth is short and differs only in `$1,200.00` against `$1,250.00`, so its matching (1 × 1) would break the shared total. Its Differs entry has the header `old file paragraph 5, file line 9; new file paragraph 5, file line 9`, its `old:` and `new:` lines, then Line A, and no word-difference line; the result line counts `Differs 3`; no line holds `no difference` in any case.
- T35 matching limit, Hidden or look-alike characters entry (Q-C13): each file is one line, one paragraph of 501 pieces: `a`, then 499 copies of `w`, then `z`, with single spaces between; in the second file `a` and `z` are each followed by U+200B. The words are equal, so the paragraphs pair as `equal` (4.2) and reach 4.3; the pieces differ at the first and the last place, so the lists after the shared start and end are 501 each, 501 × 501 = 251,001, over 250,000. Exactly one entry: `1. Hidden or look-alike characters: old file paragraph 1, file line 1; new file paragraph 1, file line 1`, then Line B, and no run-of-pieces line; the result line counts `hidden or look-alike characters 1` and 0 for the rest; no line holds Line A's `words, figures and dates`, and none holds `no difference`, in any case. With 498 copies of `w` (500 pieces each) the matching is 250,000, runs, and the entry lists its two runs of pieces, `old "a", new "a<U+200B>"` and `old "z", new "z<U+200B>"`, with no detail line.

The suite runs on Python 3.9 and the latest 3.x, and the command is also run by hand with hostile arguments (a newline in a path, an unknown option, a closed standard output).

## 10. Phases

The GC accepted section 2 and building phase 1 before the later phases are settled (Q-C11). Phases 2 to 5 are later phases, GC answered 2026-11-11; they are recorded here, not specified.
1. This spec: plain text and Markdown, sections 2 to 9. Building it also updates AGENTS.md's Status section, the README and the CHANGELOG, which describe it as comparing two files' text (Q-C1), and that wording is reviewed before release.
2. Margin line numbers (Q-C2): kept as text by default; an explicit option may ignore a leading number column, and the header then says so; never used as locations.
3. DOCX (Q-C8), read with `zipfile` and `xml` from the standard library with entity expansion refused: a file with tracked changes is refused unless a view is named (`--docx-view accepted` or `original`), printed in the header; footnotes and endnotes are text; headers and footers are compared in entries labelled as such; comments are not text, though a later option may list them, labelled "comment"; the header lists the parts read.
4. PDF (Q-C9), after a decision on reading it (the standard library cannot read text from a PDF): all text by default, stamps and running headers included, with an option to ignore repeated page headers and footers that the header names; the report says PDF text can be incomplete or out of order and that a comparison does not show a copy is the one the court holds; a page with no text layer is listed by number, never matched as empty, and a PDF with no text layer exits 2 naming the file.
5. More than two files, to follow one term through every version (Q-C10, item 3).

## 11. Questions for the GC

Q-C1 to Q-C11 were answered on 2026-11-11 in `2026-11-04-gc-reply-flt-compare-drafts.md`, and this draft applies them: Q-C1 typical uses, N8 and the "compare two files' text" wording; Q-C2 N6 and the file-location labels (5.2), and phase 2; Q-C3 the Hidden or look-alike characters label; Q-C4 the extended section 6 list; Q-C5 N2, N4, N7, the help's first line and the detail line; Q-C6 N5 and 5.1's streams; Q-C7 the help sentence and the header hashes; Q-C8 and Q-C9 phases 3 and 4; Q-C10 the header (5.2), short tokens (4.2) and phase 5; Q-C11 sections 2 and 10.

Q-C12 (three edges of those answers) was answered on 2026-11-11 in the Status Log of `2026-11-11-cto-questions-for-gc-flt-compare-drafts-q-c12.md`, and this draft applies it: (a) the scope of the section 6 list, the fixed lines outside it, and T24; (b) the result line's count `hidden or look-alike characters` and N7's first sentence, with 5.3's `as code points:` kept; (c) side-by-side words meet Q-C10 (4.2), the 4.4 detail line says what is not listed, and T34.

Q-C13 (two places the detail line also appears) was answered on 2026-11-11 in the Status Log of `2026-11-11-cto-questions-for-gc-flt-compare-drafts-q-c13.md`, and this draft applies it with her sentences verbatim: (a) the detail line is reworded as one constant for one paragraph or a run (Line A); (b) a Hidden or look-alike characters entry past the limit carries its own fixed line (Line B); both are outside the section 6 list by name, and T24 checks them byte for byte (4.4, 6, T35).

No question is open.
