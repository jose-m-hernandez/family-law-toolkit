# family-law-toolkit

Tools for people preparing California family-law paperwork. Today: a guideline child-support calculator (steps 1 and 2: the support amount, and its allocation per child), and a command that compares two files' text. Not built yet: assembling exhibit packets and binders.

Educational; not legal advice; not certified for court filing; consult counsel.

Early development, and not ready for other people to use. This repository is
private and not yet published. Two commands exist: steps 1 and 2 of a guideline
child-support calculator, and a command that compares two files' text. Nothing
else is built yet.

- What changes, and when: [CHANGELOG.md](CHANGELOG.md)
- How changes are made: [CONTRIBUTING.md](CONTRIBUTING.md)

## Running it

Needs Python 3.9 or later and nothing else to install. CI runs the tests on 3.9 and on the latest 3.x.

Run it from the repository root, the folder that contains `family_law_toolkit/`:

    python3 -m family_law_toolkit.support --a-ndi 6919.09 --b-ndi 2255.71 --a-time-percent 35 --children 2 --minimum-wage-hourly 21.00

The numbers are invented. It prints a text report to the terminal. Add `--help` to see what each flag means.

You enter net disposable income yourself. This version does not work it out from deductions (FC 4059).

For help working out the figures for your own case, you can ask a lawyer, your court's self-help center, or its family law facilitator.

## Comparing two files' text

This command compares two files' text and lists the differences it finds, so you can read each one for yourself. It reads two UTF-8 plain-text or Markdown files, up to 200,000 bytes each. PDF and Word files are not read.

Run it from the repository root, with the same Python as above:

    python3 -m family_law_toolkit.compare --old notes/parent-a-letter-1.txt --new notes/parent-a-letter-2.txt

The file names are invented. "Old" and "new" are only labels you choose; the tool does not check which file is older. It prints a plain-text report to the terminal: each file's path, byte size and sha256, then the differences in the text, by paragraph and then by word. Differences in spacing, line ends, the byte-order mark, and hidden or look-alike characters are listed separately. The exit status is 0 when the two files are identical byte for byte, 1 when they differ, and 2 when the comparison could not run. Add `--help` to see what each flag means.

What it does not do:

- It does not say whether any difference matters.
- It reads plain text only. Fonts, bold, italics, page layout, checked boxes and form fields are not compared, and Markdown markup is read as ordinary characters. If a file was made from a PDF or a form, checked boxes, form fields, stamps and signatures may be missing from it.
- It does not track moves: a paragraph that moved, or the paragraphs it moved past, may be listed as only in old at one place and only in new at another.
- It does not know which file is older, or who wrote either file, or when.
- Its paragraph and line numbers count each file as saved. They are not the paper's own numbered paragraphs, or the page and line numbers of a printed copy.
- Spacing and hidden or look-alike characters are not compared inside a paragraph whose words differ, and blank lines next to such a paragraph are not compared, except at the end of a file.
- A very long run of differing paragraphs is refused, and past this tool's matching limit an entry says that its word detail is not shown.

The report can repeat text from both files and prints their paths as you typed them. Keep it as private as the files.

For help with what a difference means for your own case, you can ask a lawyer, your court's self-help center, or its family law facilitator.

## Licence

Copyright © 2026 Jose Miguel Hernandez. Licensed under the GNU Affero General Public License v3.0 or later (see [LICENSE](LICENSE)). A commercial licence is also available from the copyright holder.

## Development

Run the tests:

    python3 -m unittest discover -s tests -t . -v

The tests use invented data.

CI also runs a private-string scan on every push and pull request; contributors do not run it, CI does. How it works and how to try it: [docs/barred-strings-scan.md](docs/barred-strings-scan.md).
