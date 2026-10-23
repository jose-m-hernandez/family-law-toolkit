# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- README, AGENTS.md (the instructions your AI agent reads) and this changelog.
- The AGPL-3.0 licence text.
- Contributing and security policies, code owners and a pull request template.
- Two decision records: how the AI-agent instructions file is arranged, and this changelog's format.
- A CI scan that fails a push or pull request if any entry from a private list appears in its history or branch name. It never prints the match. See docs/decisions/2026-10-19-every-push-and-pull-request-runs-the-barred-strings-scan.md. An entry still matches when its words are separated by a line break or repeated spaces, or when an invisible character is inserted into it; author and committer emails are checked.
- The scan can match a short entry as a whole word only, through an optional per-entry flag.
- docs/barred-strings-scan.md: how the scan works and how to try it.
- A guideline child-support calculator, step 1: the Family Code section 4055 formula on user-entered net disposable income, with hand-derived test cases and a text report.
- A CI check that fails a pull request unless CHANGELOG.md gains at least one new entry under "## [Unreleased]" (or the change is a release that moves those entries into a dated section). It prints counts only. Removing one entry and adding another counts as no change, so keep the old line or add a second.
- Tests that pin six more behaviours of the CHANGELOG check: trailing spaces after a heading, tab and nested bullets, repeated entries in a release, and exit 2 on an unexpected internal error.

### Changed

- SECURITY.md now promises a best-effort reply to a private report, not a guaranteed one.
- CONTRIBUTING.md now says every change is reviewed independently before it lands.
- The support report names the state minimum wage (Lab. Code 1182.12), states what the low-income presumption is, and notes that the per-child allocation is not shown when there are two or more children.
- AGENTS.md and the README now say that one command ships, step 1 of the child-support calculator, and that comparing drafts and assembling exhibit packets and binders do not exist yet.
