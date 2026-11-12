# family-law-toolkit

Tools for people preparing California family-law paperwork. Today: a guideline child-support calculator (steps 1 and 2: the support amount, and its allocation per child), and a command that compares two files' text. Not built yet: assembling exhibit packets and binders.

Educational; not legal advice; not certified for court filing; consult counsel.

Early development, and not ready for other people to use. This repository is
private and not yet published.

- What changes, and when: [CHANGELOG.md](CHANGELOG.md)
- How changes are made: [CONTRIBUTING.md](CONTRIBUTING.md)

## Running it

Needs Python 3.9 or later and nothing else to install. CI runs the tests on 3.9 and on the latest 3.x.

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

## Licence

Copyright © 2026 Jose Miguel Hernandez. Licensed under the GNU Affero General Public License v3.0 or later (see [LICENSE](LICENSE)). A commercial licence is also available from the copyright holder.

## Development

Run the tests:

    python3 -m unittest discover -s tests -t . -v

The tests use invented data.

CI also runs a private-string scan on every push and pull request; contributors do not run it, CI does. How it works and how to try it: [docs/barred-strings-scan.md](docs/barred-strings-scan.md).
