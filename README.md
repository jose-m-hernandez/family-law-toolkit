# family-law-toolkit

Tools for people working with California family-law documents. Today: a guideline child-support calculator (steps 1 and 2: the support amount, and its allocation per child), a command that compares two files' text, a counter of months that have five of a chosen weekday, a calendar that numbers the weeks of a month, and two optional PDF tools: one renders chosen pages of a PDF to PNG images, one renders Markdown tables to a PDF.
Educational; not legal advice; not certified for court filing; consult counsel.

Version 0.1.0. Six tools; each section below gives what it does, the exact command, an example on invented data, and what it does not do.

- What changes, and when: [CHANGELOG.md](CHANGELOG.md)
- How changes are made: [CONTRIBUTING.md](CONTRIBUTING.md)

## What you need

| Tool | Language | What to install | Command, from the repository root |
|---|---|---|---|
| Child-support calculator | Python | Python 3.9 or later; nothing else | `python3 -m family_law_toolkit.support` |
| Compare two files' text | Python | Python 3.9 or later; nothing else | `python3 -m family_law_toolkit.compare` |
| Fifth-week counter | JavaScript | Node.js 22 or later; nothing else | `node js/nth-week.js` |
| Week calendar | JavaScript | Node.js 22 or later; nothing else | `node js/week-calendar.js` |
| page-render (optional) | Python | Python 3.9 or later, pypdf, and poppler | `python3 pdf/page-render/page_render.py` |
| md-table-pdf (optional) | Python | Python 3.9 or later, reportlab and pypdf; macOS only | `python3 pdf/md-table-pdf/md_table_pdf.py` |

## Running it

Needs Python 3.9 or later and nothing else to install, for every command except the optional PDF tools under `pdf/`, which list what they need below. CI runs the tests on 3.9 and on the latest 3.x. The fifth-week counter and the week calendar are the other exceptions: both are JavaScript, they need Node.js 22 or later, and they need nothing else to install.

Run it from the repository root, the folder that contains `family_law_toolkit/`:

    python3 -m family_law_toolkit.support --a-ndi 9500.00 --b-ndi 3500.00 --a-time-percent 15 --children 3 --minimum-wage-hourly 21.00

The numbers are invented. You type net disposable income yourself; the tool never computes tax. It prints a text report to the terminal. Add `--help` to see what each flag means.

With the numbers above, the report reads:

    family-law-toolkit v0.1.0 — not certified for court filing; not affiliated with DissoMaster or XSpouse

    Guideline child support (California Family Code section 4055)
    Amounts are monthly dollars, rounded to the nearest cent (halves round up).

    Inputs as given
      Parent A net disposable income: 9500.00
      Parent B net disposable income: 3500.00
      Parent A's share of time: 15%
      Number of children: 3
      Hourly state minimum wage used (Lab. Code 1182.12): 21.00

    Formula
      Total net disposable income, TN (FC 4055(b)(1)(E)): 13000.00
      High earner (FC 4055(b)(1)(C)): Parent A
      High earner's share of time, H% (FC 4055(b)(1)(D)): 15%
      K table row (FC 4055(b)(3)): 4
      K (FC 4055(b)(3)): 0.247604
      HN, the high earner's net disposable income: 9500.00
      Formula result, CS = K[HN - (H%)(TN)] (FC 4055(a)): 1869.41
      Children multiplier (FC 4055(b)(4)): 2
      CS times multiplier (FC 4055(b)(4)): 3738.82
      Paying parent (FC 4055(b)(5)): Parent A
      Support amount (FC 4055(a), (b)(4)): 3738.82

    Low-income adjustment (FC 4055(b)(7); range under FC 4055(c))
      Threshold (FC 4055(b)(7)): 3640.00 = hourly minimum wage x 40 x 52 / 12
      The paying parent's net disposable income is not less than the threshold, so the low-income adjustment does not apply (FC 4055(b)(7)).

    Additional child support (FC 4062)
      No additional child support costs were entered. This report does not say that none apply.

    You enter net disposable income yourself. This version does not work it out from deductions (FC 4059).
    You enter the share of time yourself. The default-proceeding rule (FC 4055(b)(6)) is not applied.
    The per-child allocation (FC 4055(b)(8)) is shown only if you add --same-time-sharing-arrangement yes. It does not apply when the children have different time-sharing arrangements.

    This report is arithmetic on the figures you entered. It is not legal advice.

You enter net disposable income yourself. This version does not work it out from deductions (FC 4059).

For help working out the figures for your own case, you can ask a lawyer, your court's self-help center, or its family law facilitator.

What it prints, and when it stops:

- On success it writes the report to standard output, writes nothing to standard error, and exits with status 0. `--help` also exits with status 0.
- A flag that is missing, a flag it does not know, or a value it cannot read writes a message naming the problem to standard error, writes nothing to standard output, and exits with status 2.

Limits:

- You type net disposable income. The tool never computes tax or deductions, and does not apply FC 4059.
- You type the share of time. The default-proceeding rule (FC 4055(b)(6)) is not applied.
- The per-child allocation is shown only with `--same-time-sharing-arrangement yes`, only with two or more children, and only when all the children share one arrangement. Different shares for different children together with that flag is an error, which exits with status 2 and prints nothing on standard output.
- It is arithmetic on the figures you enter. It is not legal advice.
- FC means the California Family Code. FC 4055 is the section the calculator follows.

### Adding costs on top of guideline support

The calculator has five more optional flags: two for monthly costs that FC 4062(a) names (childcare costs, and uninsured health care costs for the children), and three for how those costs are divided between the two parents:

- `--childcare-monthly AMOUNT` is the monthly childcare cost (FC 4062(a)(1)).
- `--uninsured-health-monthly AMOUNT` is the monthly uninsured health care cost for the children (FC 4062(a)(2)).
- `--a-adjusted-ndi AMOUNT` and `--b-adjusted-ndi AMOUNT` are each parent's net disposable income as you worked it out after any spousal-support adjustment, not reduced for child support. Give both, or neither.
- `--a-cost-share-percent PERCENT` is Parent A's share of the costs, if you choose the split yourself instead of giving the two adjusted figures.

Give at least one cost, and then either both adjusted figures or `--a-cost-share-percent`. With the adjusted figures, the report reduces the paying parent's figure by the support amount it printed (FC 4061(d)) and divides the costs in proportion to the two figures (FC 4061(a), (b)(2)). A run that gives a cost without a way to split it, or an option that would go unused, stops with exit status 2 and one line on standard error.

The numbers are invented:

    $ python3 -m family_law_toolkit.support --a-ndi 5000.00 --b-ndi 3000.00 --a-time-percent 20 --children 1 --minimum-wage-hourly 21.00 --childcare-monthly 600.00 --uninsured-health-monthly 120.00 --a-adjusted-ndi 5000.00 --b-adjusted-ndi 3000.00

The additional-costs part of the report reads:

    Additional child support (FC 4062), split under FC 4061
      Costs you entered, monthly:
        Childcare costs related to employment or to reasonably necessary education or training for employment skills (FC 4062(a)(1)): 600.00
        The reasonable uninsured health care costs for the children (FC 4062(a)(2)): 120.00
        Total: 720.00
      Net disposable income figures used (you entered them; this report did not adjust them):
        Parent A, as you entered it: 5000.00
        Parent B, as you entered it: 3000.00
      Basic support is taken first (FC 4061(b)(1)); then the paying parent's figure is reduced by it (FC 4061(d)):
        Parent A, the paying parent in this report: 5000.00 - 1020.00 = 3980.00
        Parent B is not increased by support received: 3000.00
      Split in proportion to those figures (FC 4061(a), (b)(2)):
        Parent A: 3980.00 / 6980.00 = 57.02%: 410.54
        Parent B: 3000.00 / 6980.00 = 42.98%: 309.46

The tool never works out income and never says which costs count, whether a cost is actually incurred or reasonable, or what any court will order. For those questions you can ask a lawyer, your court's self-help center, or its family law facilitator.

## Comparing two files' text

This command compares two files' text and lists the differences it finds, so you can read each one for yourself. It reads two UTF-8 plain-text or Markdown files, up to 200,000 bytes each. PDF and Word files are not read.

Run it from the repository root, with the same Python as above:

    python3 -m family_law_toolkit.compare --old docs/examples/letter-a.txt --new docs/examples/letter-b.txt

The two files are invented letters kept in this repository. "Old" and "new" are only labels you choose. The command prints a plain-text report to the terminal: each file's path, byte size and sha256, then the differences in the text, by paragraph and then by word. Differences in spacing, line ends, the byte-order mark, and hidden or look-alike characters are listed separately, except in the places listed under "What it does not do" below. The entries are labelled "Differs", "Only in old" and "Only in new" for paragraphs, with their own labels for spacing, hidden or look-alike characters, and the files as a whole.

The exit status is 0 when the two files are identical byte for byte, 1 when they differ, and 2 when the comparison could not run. Add `--help` to see what each flag means.

For the two example letters, the command exits with status 1 and writes nothing to standard error. The report is:

    family-law-toolkit v0.1.0 — not certified for court filing

    Comparison of two text files
    Educational; not legal advice; not certified for court filing; consult counsel.

    Files
      Old (--old): docs/examples/letter-a.txt
        221 bytes; 9 lines; 5 paragraphs; byte-order mark: no; line ends: LF
        sha256: e4f6d53f8e50e7baa65ea5f721b287dafeec48d533e05fd5004ef2656f85abfa
      New (--new): docs/examples/letter-b.txt
        266 bytes; 11 lines; 6 paragraphs; byte-order mark: no; line ends: LF
        sha256: eef36822750724a401f7b8530690221bbf72dc1d935c1611c01ad6827be41754

    Result: the files differ. Differs 2, only in old 0, only in new 0, spacing 0, hidden or look-alike characters 0, file 0.

    Differences
      1. Differs: old file paragraph 2, file line 3; new file paragraph 2, file line 3
         old: The community hall will be open on Saturday morning for the seed
           swap.
         new: The community hall will be open on Sunday morning for the seed swap.
         - old file line 3, new file line 3: old "Saturday", new "Sunday", after
           "be open on"
      2. Differs: old file paragraph 4, file line 7; new file paragraphs 4-5, file lines 7-9
         old: We will meet again on the first Friday of next month.
         new: We will meet again on the first Monday of next month.
         new: Tea and biscuits will be offered at the door.
         - old file line 7, new file line 7: old "Friday", new "Monday", after "on
           the first"
         - new file line 9: only in new (paragraph break) "Tea and biscuits will
           be offered at the door.", after "of next month."

    Notes
      This report lists differences in the text of the two files. It does not say
      whether any difference matters.
      It reads both files as plain text. Fonts, bold, italics, page layout,
      checked boxes and form fields are not compared, and Markdown markup is read
      as ordinary characters.
      Moves are not tracked: a paragraph that moved, or the paragraphs it moved
      past, may be listed as only in old at one place and only in new at another.
      "Old" and "new" are the labels you gave. This tool does not check which file
      is older, who changed either file, when, or whether either was filed or
      served.
      This report can repeat text from both files and prints their paths as you
      typed them. Keep it as private as the files.
      Paragraph and line numbers in this report count the paragraphs and lines of
      each file as saved (lines end at LF, CR or CRLF). They are not the paper's
      own numbered paragraphs, or the page and line numbers of a printed or filed
      copy.
      Spacing and hidden or look-alike characters are not compared inside a
      Differs entry. Blank lines are not compared at, just before or just after a
      Differs, Only in old or Only in new entry, except at the end of a file. When
      both files use the same kinds of line end and their text differs elsewhere,
      where the line ends sit is not compared.
      If a file was made from a PDF or a form, checked boxes, form fields, stamps
      and signatures may be missing from it. This report covers only the text in
      the two files.

Both letters are invented. The report lists two differences: one changed word ("Saturday" and "Sunday"), and one changed day ("the first Friday" and "the first Monday") followed by a paragraph that is only in the new letter.

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

Every month holds at least four of each weekday, and some hold a fifth. A month is 28 to 31 days long, which is four whole weeks plus up to three extra days, and those extra days decide which weekdays turn up five times. Many recurring arrangements are written in terms of the first, third or fifth week of a month: a class that meets on the fifth Tuesday, a committee that meets on the first and third Monday. The fifth is the awkward one, because it exists only in some months.

Which months have a fifth one changes from year to year, and it is different for each weekday, so it cannot be read off a single calendar. This command lists them. Choose a weekday and a range of years, and it prints every date that is the fifth occurrence of that weekday in its month, so the pattern can be seen before a rule of thumb is relied on. The example further down does this for Tuesdays in 2031 and finds four.

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

It lists 2031-04-29, 2031-07-29, 2031-09-30 and 2031-12-30. It exits with status 0. The label line below goes to standard error, and standard output is as follows (its first line is empty):

    5th week counter (weeks numbered from the first week that contains the anchor weekday)
    Range: 2031–2031
    Definition: Week 1 is the first week that contains a Tuesday. A month has a "5th week" if it contains 5 Tuesdays.
    Showing dates and per-year summary.
    2031-04-29
    2031-07-29
    2031-09-30
    2031-12-30
    Year 2031: 4 months
    Tuesday (2) → Months with a 5th week (first week contains Tuesday): 4 (between 2031 and 2031).
    Summary for Tuesday: total months=4, years=1, avg/year=4.00, median/year=4, min/year=4, max/year=4

Dates are calendar dates, and they print the same on a computer in any time zone.

What it prints, and when it stops:

- Every run first writes the line `Educational; not legal advice; not certified for court filing; consult counsel.` to standard error.
- A run that cannot go ahead writes a message naming the problem and the usage to standard error, writes nothing to standard output, and exits with status 1. That covers: no weekday, a weekday or name it does not recognise, both `--anchor` and `--weekday`, a year or range outside the rules above, a flag with no value, a flag given twice, a word that is not a flag, and a flag it does not know.
- Its `--help` names the file `nth-week.js`, so from the repository root give the path `js/nth-week.js`.

## Numbering the weeks of a month

A schedule or an order might say that something happens in "the second week" of the month, or in weeks 1 and 3. Which dates those are depends on which week counts as week 1. Weeks run Sunday to Saturday, and week 1 is the week that contains the month's first one of the weekday you choose. In April 2031, counted from the first week that contains a Thursday, week 2 runs Sunday 6 April to Saturday 12 April. An order may or may not say which weekday it counts from, so this command lets you see the weeks for the weekday you choose.

It numbers the weeks of one month from the weekday you choose, lists each week's dates, and can also print the dates of chosen weekdays in every week and the month as a grid. It does not read an order, decide which weekday an order counts from, or say who has which day. Weeks run Sunday to Saturday only.

Choosing the weekday and the month:

- `--anchor` with one weekday name is required (for example `Thursday` or `Thu`, in any case). `--anchor` names the weekday that week 1 must contain: week 1 is the Sunday-to-Saturday week that holds the month's first one (the first Thursday, if you gave `Thursday`); week 2 holds the second, and so on. A month has as many numbered weeks as it has of that weekday, 4 or 5, so a month has a week 5 exactly when the counter above finds a fifth one of that weekday in it.
- Give the year and then the month: the year is a whole number from 1583 to 9999, and the month is a whole number from 1 (January) to 12 (December), so `4` and `04` both mean April. Flags may come before or after them.
- Spaces around a value or a list item are ignored; a tab or line break is an error.
- Each flag is given once.

Choosing what else to print:

- `--day` takes weekday names, comma-separated (for example `Monday,Saturday`), and prints that weekday's date in every week. Each weekday is printed once, Sunday first, whatever order you gave them in. A Saturday and the Sunday after it fall in different weeks, because every week starts on Sunday.
- `--grid` adds the month as a grid. The row of each numbered week begins with its number; days outside the numbered weeks sit on rows with no number.

Days of the month before week 1 and after the last week belong to no numbered week; they are listed after the weeks, and before the grid when `--grid` is given.

Run it from the repository root. It is JavaScript, so it runs with `node`, not `python3`. The full form is:

    node js/week-calendar.js <year> <month> --anchor <weekday> [--day <weekdays>] [--grid]

For example:

    node js/week-calendar.js 2031 4 --anchor Thursday --grid

It prints:

    Weeks of April 2031, numbered from the first week that contains a Thursday
    Each week runs Sunday to Saturday.

    Week 1: Sun Mar 30 2031 - Sat Apr 05 2031
    Week 2: Sun Apr 06 2031 - Sat Apr 12 2031
    Week 3: Sun Apr 13 2031 - Sat Apr 19 2031
    Week 4: Sun Apr 20 2031 - Sat Apr 26 2031

    April 2031 has 4 Thursdays, so it has 4 numbered weeks.
    Days of April 2031 before week 1: none.
    Days of April 2031 after week 4: Sun Apr 27 2031 - Wed Apr 30 2031.

    April 2031
           Sun Mon Tue Wed Thu Fri Sat
    Week 1           1   2   3   4   5
    Week 2   6   7   8   9  10  11  12
    Week 3  13  14  15  16  17  18  19
    Week 4  20  21  22  23  24  25  26
            27  28  29  30

Week 1 can start in the month before, as it does here. That run exits with status 0, and writes the label line below to standard error.

Dates are calendar dates, and they print the same on a computer in any time zone.

What it prints, and when it stops:

- Every run first writes the line `Educational; not legal advice; not certified for court filing; consult counsel.` to standard error.
- A run that cannot go ahead writes a message naming the problem and the usage to standard error, writes nothing to standard output, and exits with status 1. That covers: no year or month, a year or month outside the rules above, no weekday, a weekday name it does not recognise (for `--anchor` or in a `--day` list), a flag with no value, a flag given twice, a word besides the year and the month that is not a flag or a flag's value, and a flag it does not know.
- Its `--help` names the file `week-calendar.js`, so from the repository root give the path `js/week-calendar.js`.

## PDF tools (optional)

Both tools are optional. page-render needs pypdf and poppler's `pdftoppm`, `pdfinfo` and `pdftotext`. md-table-pdf needs reportlab and pypdf to run, needs poppler only for its tests, and runs on macOS only. Install pypdf and reportlab, at the versions in `pdf/requirements.txt`, into a virtual environment outside the repository (as shown just below), and run both tools with that environment's `python`. The poppler tools are expected at `/opt/homebrew/bin` (on a Mac with Homebrew: `brew install poppler`).

Make the virtual environment in a temporary folder, outside the repository; the commands on this page reuse the folder name `OUT`:

    OUT=$(mktemp -d)
    python3 -m venv "$OUT/venv"
    "$OUT/venv/bin/python" -m pip install -r pdf/requirements.txt

page-render renders chosen pages of an image-only PDF to PNG images, so they can be read and cited. Run it from the repository root:

    python3 pdf/page-render/page_render.py notes/scan.pdf --pages 1-3 -o notes/pages

The file names are invented. It writes one PNG per page, named by the source page, plus `manifest.tsv` and `contact_sheet.html`. The environment variables `PAGE_RENDER_PDFTOPPM`, `PAGE_RENDER_PDFINFO` and `PAGE_RENDER_PDFTOTEXT` can point it at other copies of the poppler tools. page-render looks for the poppler programs in `/opt/homebrew/bin`, where Homebrew installs them on an Apple-silicon Mac; on an Intel Mac Homebrew uses `/usr/local/bin`, so set the environment variables named above. Its exit codes and checks are in `pdf/page-render/README.md`.

md-table-pdf renders Markdown pipe tables (with optional headings and paragraphs) to a landscape US Letter PDF:

    python3 pdf/md-table-pdf/md_table_pdf.py notes/table.md -o notes/table.pdf

Replace notes/scan.pdf and notes/table.md with your own files; the worked example further down needs no file of your own.

md-table-pdf runs on macOS only: it needs the Arial font that macOS keeps in /System/Library/Fonts/Supplemental, and on other systems it stops with exit status 5. Its exit codes and checks are in `pdf/md-table-pdf/README.md`.

Neither tool says what a page or table means for your case.

A worked example, on an invented file kept in this repository (`docs/examples/table.md`: a heading, a paragraph and a three-row table). It uses the virtual environment made above, and writes the PDF outside the repository, in the same temporary folder:

    "$OUT/venv/bin/python" pdf/md-table-pdf/md_table_pdf.py docs/examples/table.md -o "$OUT/table.pdf"

On macOS, with the packages installed, this exits with status 0, writes nothing to standard error, and prints the absolute path of the PDF and then:

    1 tables, 3 body rows, 1 pages

Then render page 1 of that PDF:

    "$OUT/venv/bin/python" pdf/page-render/page_render.py "$OUT/table.pdf" --pages 1 -o "$OUT/pages"

It exits with status 0. It prints four lines on standard output: `OK: rendered 1 of 1 page(s) at 200 dpi ->` followed by the folder, then `pages: 1`, then the paths of `manifest.tsv` and `contact_sheet.html`. On standard error it prints one warning, which is advisory and does not change the exit status:

    page_render: warning: page 1: text differ between pypdf and poppler

The folder holds `table-p0001.png`, `manifest.tsv` and `contact_sheet.html`. This is the manifest, with tabs between the columns; the sha256 may differ on your computer, because it depends on the poppler version:

    page	file	width_px	height_px	sha256	text_check
    1	table-p0001.png	2200	1700	8196e537de52e008561022e45e4bedcd9e789433cef355ead9d01656ab719f5b	differ

page-render stops with exit status 4 if the output folder already holds an earlier page-render result, so give it a new folder each time.

## What the tools touch

- The child-support calculator, the fifth-week counter and the week calendar read no file. They print to the terminal only.
- The compare command reads the two files you name with `--old` and `--new`, and writes to the terminal only.
- page-render reads the PDF you name. It writes into the folder you give with `-o`: the PNG images, `manifest.tsv` and `contact_sheet.html`. It also runs the poppler programs `pdftoppm`, `pdfinfo` and `pdftotext` on your computer.
- md-table-pdf reads the Markdown file you name, and the font files that macOS keeps in `/System/Library/Fonts/Supplemental`: Arial Unicode (or Arial, if that one is missing), and Arial Bold and Courier New when present. It writes the PDF you give with `-o`; without `-o` it writes the PDF next to the input file. While it works it writes a temporary file in the output folder and then renames it.
- None of the six makes a network call. A search of the Python and JavaScript files under `family_law_toolkit/`, `js/` and `pdf/` for networking modules and calls finds none outside the tests; the only match in a tool is page-render's use of `urllib.parse` to percent-encode file names in the contact sheet.

## Licence

Copyright (c) 2026 Jose Miguel Hernandez. Licensed under the GNU Affero General Public License v3.0 or later (see [LICENSE](LICENSE)). Any copying, modification or distribution beyond what that licence permits requires the copyright holder's prior written permission.

A commercial licence is available from the copyright holder.

## Development

Run the tests:

    python3 -m unittest discover -s tests -t . -v

The tests of the two JavaScript tools (the fifth-week counter and the week calendar) run on Node's built-in test runner:

    node --test --test-reporter=tap "js/**/*.test.js"

They have been run on Node 22, 24 and 26 and need Node 22 or later (the quotes matter: Node reads the pattern itself, so it finds every test file under `js/`).

The PDF tools' tests need the optional software above and run with:

    python3 pdf/run_tests.py

CI runs them on macOS in the `pdf-tests` job.

The tests use invented data.

CI also runs a private-string scan on every push and pull request; contributors do not run it, CI does. How it works and how to try it: [docs/barred-strings-scan.md](docs/barred-strings-scan.md).
