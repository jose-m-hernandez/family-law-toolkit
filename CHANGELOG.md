# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

### Changed

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
