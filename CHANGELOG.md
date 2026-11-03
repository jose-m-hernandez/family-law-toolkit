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
- A test that shows why case S5 is among the step-2 test cases: rounding each exact per-child amount to the cent on its own would add up to one cent less than the support amount shown, which is why the toolkit rounds the amount for each number of children before taking the differences.

### Changed

- SECURITY.md now promises a best-effort reply to a private report, not a guaranteed one.
- CONTRIBUTING.md now says every change is reviewed independently before it lands.
- The one-line CLAUDE.md that pointed Claude Code at AGENTS.md is removed; Claude Code now reads AGENTS.md directly.
- The support report names the state minimum wage (Lab. Code 1182.12), states what the low-income presumption is, and notes that the per-child allocation is not shown when there are two or more children.
- AGENTS.md and the README now say that one command ships, step 1 of the child-support calculator, and that comparing drafts and assembling exhibit packets and binders do not exist yet.
- `AGENTS.md` is now the only instruction file, and the decision record that kept the bridge is superseded (`docs/decisions/2026-11-02-agents-md-is-the-only-instruction-file.md`).
- A bad value on the command line now produces an error that names the flag you typed (for example `--a-ndi`), not the Python parameter (`a_ndi`). `compute()` and its error messages are unchanged.
