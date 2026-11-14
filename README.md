# family-law-toolkit

Tools for people preparing California family-law paperwork. Today: a guideline child-support calculator (steps 1 and 2: the support amount, and its allocation per child), a command that compares two files' text, a counter of months that have five of a chosen weekday, and two optional PDF tools: one renders chosen pages of a PDF to PNG images, one renders Markdown tables to a PDF. Not built yet: assembling exhibit packets and binders.

Educational; not legal advice; not certified for court filing; consult counsel.

Early development, and not ready for other people to use. This repository is
private and not yet published.

- What changes, and when: [CHANGELOG.md](CHANGELOG.md)
- How changes are made: [CONTRIBUTING.md](CONTRIBUTING.md)

## Running it

Needs Python 3.9 or later and nothing else to install, for every command except the optional PDF tools under `pdf/`, which list what they need below. CI runs the tests on 3.9 and on the latest 3.x. The fifth-week counter is the one other exception: it is JavaScript, it needs Node.js (CI uses Node 26), and it needs nothing else to install.

Run it from the repository root, the folder that contains `family_law_toolkit/`:

    python3 -m family_law_toolkit.support --a-ndi 6919.09 --b-ndi 2255.71 --a-time-percent 35 --children 2 --minimum-wage-hourly 21.00

The numbers are invented. It prints a text report to the terminal. Add `--help` to see what each flag means.

With the numbers above, the report reads:

    family-law-toolkit v0.1.0 — not certified for court filing; not affiliated with DissoMaster or XSpouse

    Guideline child support (California Family Code section 4055)
    Amounts are monthly dollars, rounded to the nearest cent (halves round up).

    Inputs as given
      Parent A net disposable income: 6919.09
      Parent B net disposable income: 2255.71
      Parent A's share of time: 35%
      Number of children: 2
      Hourly state minimum wage used (Lab. Code 1182.12): 21.00

    Formula
      Total net disposable income, TN (FC 4055(b)(1)(E)): 9174.80
      High earner (FC 4055(b)(1)(C)): Parent A
      High earner's share of time, H% (FC 4055(b)(1)(D)): 35%
      K table row (FC 4055(b)(3)): 3
      K (FC 4055(b)(3)): 0.337500
      HN, the high earner's net disposable income: 6919.09
      Formula result, CS = K[HN - (H%)(TN)] (FC 4055(a)): 1251.42
      Children multiplier (FC 4055(b)(4)): 1.6
      CS times multiplier (FC 4055(b)(4)): 2002.27
      Paying parent (FC 4055(b)(5)): Parent A
      Support amount (FC 4055(a), (b)(4)): 2002.27

    Low-income adjustment (FC 4055(b)(7); range under FC 4055(c))
      Threshold (FC 4055(b)(7)): 3640.00 = hourly minimum wage x 40 x 52 / 12
      The paying parent's net disposable income is not less than the threshold, so the low-income adjustment does not apply (FC 4055(b)(7)).

    You enter net disposable income yourself. This version does not work it out from deductions (FC 4059).
    You enter the share of time yourself. The default-proceeding rule (FC 4055(b)(6)) is not applied.
    The per-child allocation (FC 4055(b)(8)) is shown only if you add --same-time-sharing-arrangement yes. It does not apply when the children have different time-sharing arrangements.

    This report is arithmetic on the figures you entered. It is not legal advice.

You enter net disposable income yourself. This version does not work it out from deductions (FC 4059).

For help working out the figures for your own case, you can ask a lawyer, your court's self-help center, or its family law facilitator.

## Comparing two files' text

This command compares two files' text and lists the differences it finds, so you can read each one for yourself. It reads two UTF-8 plain-text or Markdown files, up to 200,000 bytes each. PDF and Word files are not read.

Run it from the repository root, with the same Python as above:

    python3 -m family_law_toolkit.compare --old notes/letter-a.txt --new notes/letter-b.txt

The file names are invented. "Old" and "new" are only labels you choose. The command prints a plain-text report to the terminal: each file's path, byte size and sha256, then the differences in the text, by paragraph and then by word. Differences in spacing, line ends, the byte-order mark, and hidden or look-alike characters are listed separately, except in the places listed under "What it does not do" below. The entries are labelled "Differs", "Only in old" and "Only in new" for paragraphs, with their own labels for spacing, hidden or look-alike characters, and the files as a whole.

The exit status is 0 when the two files are identical byte for byte, 1 when they differ, and 2 when the comparison could not run. Add `--help` to see what each flag means.

What it does not do:

- It does not say whether any difference matters.
- It reads plain text only. Fonts, bold, italics, page layout, checked boxes and form fields are not compared, and Markdown markup is read as ordinary characters. A file made from a PDF or a form may lack checked boxes, form fields, stamps and signatures.
- It does not track moves: a paragraph that moved, or the paragraphs it moved past, may be listed as only in old at one place and only in new at another.
- It does not know which file is older, who wrote either file or when, or whether either is the copy a court or another person holds.
- Its paragraph and line numbers count each file as saved. They are not the paper's own numbered paragraphs, or the page and line numbers of a printed copy.
- Some places are not compared. Spacing and hidden or look-alike characters are not compared inside a Differs entry. Blank lines are not compared at, just before or just after a Differs, Only in old or Only in new entry, except at the end of a file. When both files use the same kinds of line end and their text differs elsewhere, where the line ends sit is not compared.
- Past this tool's matching limit, an entry carries a line beginning "Detail not shown". A Differs entry then does not list the words, figures and dates that differ inside it, and a Hidden or look-alike characters entry does not list the hidden or look-alike characters that differ inside it.
- It does not compare two files when too many paragraphs lie between their first and last differences. It sets aside the paragraphs the files share at the start and at the end; if the paragraphs left between them, in the old file times in the new file, come to more than 250,000 pairs (for example, more than 500 such paragraphs in each file), it stops with exit status 2 and the message "too many paragraphs lie between the first and last differences to compare within this tool's limit". The paragraphs in between need not differ: two long files that differ only near the start and near the end can be refused even when few paragraphs differ.

The report can repeat text from both files and prints their paths as you typed them. Keep it as private as the files.

For help with what a difference means for your own case, you can ask a lawyer, your court's self-help center, or its family law facilitator.

## Counting fifth weeks

A parenting schedule may give one parent the first and third weekends of each month and the other parent the rest. Most months have four of any given weekday, but a few have five, and those fifth weekends are where the two parents' totals drift apart. Which months have one depends on the day the weekend is counted from. Friday 30 April 2027 is the fifth Friday of April, yet the next day, Saturday 1 May 2027, is the first Saturday of May. Counted from its Friday that weekend is April's fifth; counted from its Saturday it is May's first.

The yearly totals shift too. Counting by Fridays, 2027 has 5 months with a fifth Friday and 2028 has 4. Counting by Saturdays or by Sundays, 2027 has 4 and 2028 has 5. An order may or may not say which day it counts from, so this command lets you lay the choices side by side, year by year, before relying on one.

In this command, a month with five of a chosen weekday is said to have a "fifth week". The command counts those months in a range of years, and prints each date that is a fifth occurrence, a count for each year, and a summary. It counts calendar dates only: it does not read an order, build a schedule, or say who has which weekend.

Choosing the weekday (required):

- Use one of two flags, not both. Give `--anchor` with a weekday name (for example `Tuesday`, `Tue`, or `Tuesday,Wednesday`), or `--weekday` with a whole number from 0 to 6 (0 is Sunday, 1 is Monday, 2 is Tuesday, and so on), or a comma-separated list of them.
- Spaces around a value or a list item are ignored; a tab or line break is an error.
- A weekday given twice is counted once.
- With more than one weekday, each is counted separately: the output has one block of dates and one summary for each.

Choosing the years:

- `--start` and `--end` are the first and last year.
- `--end` defaults to 18 years after `--start`, and `--start` defaults to this year. With neither given, the range is this year and the 18 years after it; with `--start 2031` alone it is 2031 to 2049.
- Years must be whole numbers from 1583 to 9999. All dates use today's Gregorian calendar rules, also for years before a country adopted it (this is called the proleptic Gregorian calendar).
- `--start` must not be after `--end`, and the range can be at most 1000 years.
- `--list` and `--per-year` are accepted but change nothing: the dates and the count for each year are always printed.

Run it from the repository root. It is JavaScript, so it runs with `node`, not `python3`:

    node js/nth-week.js --anchor Tuesday --start 2031 --end 2031

It lists 2031-04-29, 2031-07-29, 2031-09-30 and 2031-12-30.

Dates are calendar dates, and they print the same on a computer in any time zone.

What it prints, and when it stops:

- Every run first writes the line `Educational; not legal advice; not certified for court filing; consult counsel.` to standard error.
- A run that cannot go ahead writes a message naming the problem and the usage to standard error, writes nothing to standard output, and exits with status 1. That covers: no weekday, a weekday or name it does not recognise, both `--anchor` and `--weekday`, a year or range outside the rules above, a flag with no value, a flag given twice, a word that is not a flag, and a flag it does not know.
- Its `--help` names the file `nth-week.js`, so from the repository root give the path `js/nth-week.js`.

## PDF tools (optional)

Both tools are optional. They need pypdf and reportlab at the versions in `pdf/requirements.txt` (install them with `python3 -m pip install -r pdf/requirements.txt`), and poppler's `pdftoppm`, `pdfinfo` and `pdftotext`, which they expect at `/opt/homebrew/bin` (on a Mac with Homebrew: `brew install poppler`).

page-render renders chosen pages of an image-only PDF to PNG images, so they can be read and cited. Run it from the repository root:

    python3 pdf/page-render/page_render.py notes/scan.pdf --pages 1-3 -o notes/pages

The file names are invented. It writes one PNG per page, named by the source page, plus `manifest.tsv` and `contact_sheet.html`. The environment variables `PAGE_RENDER_PDFTOPPM`, `PAGE_RENDER_PDFINFO` and `PAGE_RENDER_PDFTOTEXT` can point it at other copies of the poppler tools. Its exit codes and checks are in `pdf/page-render/README.md`.

md-table-pdf renders Markdown pipe tables (with optional headings and paragraphs) to a landscape US Letter PDF:

    python3 pdf/md-table-pdf/md_table_pdf.py notes/table.md -o notes/table.pdf

md-table-pdf runs on macOS only: it needs the Arial font that macOS keeps in /System/Library/Fonts/Supplemental, and on other systems it stops with exit status 5. Its exit codes and checks are in `pdf/md-table-pdf/README.md`.

Neither tool says what a page or table means for your case.

## Licence

Copyright © 2026 Jose Miguel Hernandez. Licensed under the GNU Affero General Public License v3.0 or later (see [LICENSE](LICENSE)). A commercial licence is also available from the copyright holder.

## Development

Run the tests:

    python3 -m unittest discover -s tests -t . -v

The fifth-week counter's tests run on Node's built-in test runner:

    node --test --test-reporter=tap "js/**/*.test.js"

They have been run on Node 22, 24 and 26 and need Node 22 or later (the quotes matter: Node reads the pattern itself, so it finds every test file under `js/`).

The PDF tools' tests need the optional software above and run with:

    python3 pdf/run_tests.py

CI runs them on macOS in the `pdf-tests` job.

The tests use invented data.

CI also runs a private-string scan on every push and pull request; contributors do not run it, CI does. How it works and how to try it: [docs/barred-strings-scan.md](docs/barred-strings-scan.md).
