# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- The `support` command takes five more optional inputs for additional child support (FC 4062): `--childcare-monthly`, `--uninsured-health-monthly`, `--a-adjusted-ndi`, `--b-adjusted-ndi` and `--a-cost-share-percent`. Given a cost, the report splits it between the parents in proportion to the two adjusted net disposable income figures you type, after reducing the paying parent's figure by the basic support the report printed (FC 4061(d)), at each end of the range when the support amount is a range; or by the split you type. It does not adjust income for spousal support and does not say which costs count. A cost without a way to split it, an unused option, a repeated option, or a figure that leaves no share to work out is refused with one line on standard error and exit status 2.
- `support --help` lists the five new options, carries the statute's own sentences for the two cost options, and gains a second example, with costs, on invented numbers.
- README: a subsection on the five new options, with an example and its printed section on invented numbers; a test checks that the printed section equals what the command prints.
- `docs/sources/` holds FC 4061 and FC 4062 beside FC 4055, and `tests/test_sources.py` pins the sha256 of all four new files and checks each `.txt` against its `.xml`.
- `docs/specs/add-ons.md` and `docs/derivations/add-ons.md`: the behaviour spec for the new section and the hand derivations its tests check, on invented numbers.
- A skill, `skills/support-calculator/SKILL.md`, for Claude Code and Codex, wired to the one source file by tracked symlinks at `.claude/skills/support-calculator` and `.codex/skills/support-calculator`. `tests/test_skill.py` fails if a wired path stops resolving to the source or the skill names a command or flag that does not exist. See `docs/decisions/2026-11-19-the-calculator-skill-has-one-source-file.md`.
- Python API: `GuidelineResult` has one more field, `additional` (None unless the command attached a split); `compute()` is unchanged. The new module `family_law_toolkit.support.additional` does the split.

### Changed

- Every `support` report now prints an additional-child-support section after the low-income section: the split when a cost is given, or a line saying no cost was entered. Every existing invocation keeps exit status 0 and gains only those lines, so the golden reports in `tests/golden/guideline_step1_reports.json` gain three lines each.
- The `support` parser has eleven options: the five required ones and six optional ones, up from six.
- `.gitignore` tracks the two skill symlinks and keeps ignoring the rest of `.claude/skills/` and `.codex/`.
- AGENTS.md: the Status paragraph describes the new optional inputs and the new section.

## [0.1.0] - 2026-11-19

### Added

- README, AGENTS.md (the instructions your AI agent reads) and this changelog.
- The AGPL-3.0 licence text.
- Contributing and security policies, code owners and a pull request template.
- Decision records in `docs/decisions/`, covering the agent instruction file, the changelog format, and the barred-strings scan.
- A CI scan that fails a push or pull request if any entry from a private list appears in its history or branch name. It never prints the match. See docs/decisions/2026-10-19-every-push-and-pull-request-runs-the-barred-strings-scan.md. An entry still matches when its words are separated by a line break or repeated spaces, or when an invisible character is inserted into it; author and committer emails are checked.
- The scan can match a short entry as a whole word only, through an optional per-entry flag.
- docs/barred-strings-scan.md: how the scan works and how to try it.
- A guideline child-support calculator, step 1: the Family Code section 4055 formula on user-entered net disposable income, with hand-derived test cases and a text report.
- A CI check that fails a pull request unless CHANGELOG.md gains at least one new entry under "## [Unreleased]" (or the change is a release that moves those entries into a dated section). It prints counts only. Removing one entry and adding another counts as no change, so keep the old line or add a second.
- Tests that pin six more behaviours of the CHANGELOG check: trailing spaces after a heading, tab and nested bullets, repeated entries in a release, and exit 2 on an unexpected internal error.
- The child-support calculator, step 2: with two or more children and the new `--same-time-sharing-arrangement yes` flag (all children share one time-sharing arrangement), the report shows the FC 4055(b)(8) allocation per child. When the low-income adjustment applies, it shows the allocation at both ends of the range. The per-child amounts add up to the support amount, or to each end of the range.
- `docs/sources/`: the text of FC 4055 that the calculator follows, with where it comes from and how to check it.
- Python API: `compute()` takes a sixth, optional argument, `same_time_sharing_arrangement` ("yes", "no" or None, the default), and its result carries a field of the same name. A call with five arguments returns the same computed values as before, and the new field is None. The new function `allocation(result)` returns the per-child allocation, or None unless there are two or more children, the argument is "yes", and a parent pays.
- A test for case S5: rounding each exact per-child amount to the cent separately adds up to one cent less than the support amount shown, which is why the toolkit rounds the amount for each number of children before taking differences.
- `python3 -m family_law_toolkit.support --help` (or `-h`) now prints what each flag means, with an example on invented numbers, and exits 0. A usage error now ends with a pointer to `--help`. The parser still has exactly six options.
- README: how to run the calculator, from the repository root, with an example command on invented numbers and the Python version it needs (3.9 or later).
- The child-support calculator takes one share of time per child: repeat `--a-time-percent` once per child (for example `--a-time-percent 30 --a-time-percent 40 --children 2`). H% is then the average of the high earner's shares (FC 4055(b)(1)(D)), used exactly in the formula and shown to two decimals. If the shares differ, no per-child allocation is shown, and adding `--same-time-sharing-arrangement yes` is an error. Giving `--a-time-percent` once works as before.
- Python API: `compute()` also accepts `a_time_percent` as a list or tuple of decimal strings, one per child, and its result carries `a_time_percent_by_child` (None when one value is given). A call made the old way returns the same computed values as before.
- README and `--help`: one sentence on where to ask for help working out the figures for your own case.
- Each Python source file states its licence (SPDX AGPL-3.0-or-later) and copyright holder, and the README names the holder.
- A command that compares two files' text: `python3 -m family_law_toolkit.compare --old FILE --new FILE`. It reads two UTF-8 plain-text or Markdown files and prints a plain-text report of their differences. The exit status is 0 when the files are identical byte for byte, 1 when they differ, and 2 when the comparison could not run. It does not say whether any difference matters.
- A fifth-week counter in JavaScript: `node js/nth-week.js`. It needs Node.js and no packages to install. It counts the months, in a range of years, that contain five of a chosen weekday, and prints each such date, a count per year and a summary. `--anchor` or `--weekday` is required. It checks its input: `--weekday` takes whole numbers 0 to 6; `--anchor` takes known weekday names only; giving both, an unknown name, a flag with no value, a value flag given twice, a stray word that is not a flag, or an unknown flag is an error; spaces around a value or a list item are ignored, a tab or line break is an error; years must be whole numbers from 1583 to 9999 (Gregorian calendar, with today's rules also for years before a country adopted it), start no later than end, at most 1000 years; `--end` defaults to `--start` plus 18. A bad input prints a message and the usage to standard error, nothing to standard output, and exits 1. Dates are calendar dates and print the same in every time zone. A weekday given twice is counted once, and with several weekdays each is counted separately, which the output now says ("5 of the same weekday"). Its tests run on Node's built-in test runner (every test file under `js/`) in a new CI job, `node-tests`, and the rule for JavaScript tools is recorded in `docs/decisions/2026-11-13-javascript-tools-live-in-js-and-use-only-node.md`.
- Two optional PDF tools under `pdf/`: `pdf/page-render/page_render.py` renders chosen pages of a PDF to PNG images and writes a manifest and an HTML contact sheet, and `pdf/md-table-pdf/md_table_pdf.py` renders Markdown pipe tables to a landscape US Letter PDF. page-render needs pypdf and poppler; md-table-pdf needs reportlab and pypdf to run, and poppler only for its tests, and it runs on macOS only. The Python packages are pinned in `pdf/requirements.txt`. Their tests run in a new macOS CI job, `pdf-tests`, which fails if it finds no tests, and the rule is recorded in `docs/decisions/2026-11-13-the-core-uses-only-the-standard-library-and-tools-needing-more-live-under-pdf.md`.
- A week calendar in JavaScript: `node js/week-calendar.js <year> <month> --anchor <weekday> [--day <weekdays>] [--grid]`. It needs Node.js and no packages to install. It numbers the Sunday-to-Saturday weeks of one month from the first week that contains the chosen weekday (a month has 4 or 5 numbered weeks), prints each week's dates, and lists the days of the month before week 1 and after the last week. `--day` also prints chosen weekdays' dates in every week, Sunday first, and `--grid` adds the month as a grid. The year is a whole number from 1583 to 9999, the month 1 to 12, `--anchor` is required and takes one weekday name, spaces around a value are ignored, and each flag is given once. A run that cannot go ahead prints a message and the usage to standard error, prints nothing to standard output, and exits 1. Dates are calendar dates, the same in every time zone. `js/utils/date.js` gains three helpers: `monthNames`, `addDays` and `formatDayLong`. It numbers calendar weeks only and does not say what any schedule, order or week number means for your case.

### Changed

- The README section "Counting fifth weeks" opens with what the command counts for a weekday the reader chooses. No command behaves differently.
- SECURITY.md now promises a best-effort reply to a private report, not a guaranteed one.
- CONTRIBUTING.md now says every change is reviewed independently before it lands.
- The one-line CLAUDE.md that pointed Claude Code at AGENTS.md is removed; Claude Code now reads AGENTS.md directly.
- The support report names the state minimum wage (Lab. Code 1182.12), states what the low-income presumption is, and notes that the per-child allocation is not shown when there are two or more children.
- AGENTS.md and the README now say that two commands ship, the child-support calculator and the comparison of two files' text, and that assembling exhibit packets and binders does not exist yet.
- `AGENTS.md` is now the only instruction file, and the decision record that kept the bridge is superseded (`docs/decisions/2026-11-02-agents-md-is-the-only-instruction-file.md`).
- A bad value on the command line now produces an error that names the flag you typed (for example `--a-ndi`), not the Python parameter (`a_ndi`). `compute()` and its error messages are unchanged.
- Giving `--a-time-percent` more than once no longer keeps only the last value: each value is one child's share.
- The README shows the report the example command prints.
- The support report ends with a line saying it is arithmetic on the figures entered and is not legal advice.
- The compare tests' fixture T2 uses other invented times, two code comments drop a cross-reference, and two test constants are named after the text they hold. Neither command's behaviour changes.
- The compare tests' fixture T2 uses another pair of invented times, and the matching example in the compare spec uses the same pair. Neither command's behaviour changes.
- The text of the compare spec (`docs/specs/compare-drafts.md`) no longer carries internal cross-references, and the README's sample report is followed by one blank line instead of two. No command behaves differently.
- The README's line on what to install now says the optional PDF tools under `pdf/` are the exception and list what they need; the core commands still need only Python 3.9 or later.
- The calculator's example cases S1 (also the example in the README and in `--help`) and G2 now have three children and new invented figures, with their expected results worked out again by hand.
