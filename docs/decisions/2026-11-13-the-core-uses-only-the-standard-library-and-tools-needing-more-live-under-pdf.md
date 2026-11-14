# The core uses only the standard library; tools that need more live under pdf/

Date: 2026-11-13

## The rule

> **The core (`family_law_toolkit/`, `ci/`, `tests/`, `js/`) uses only the standard library of its language. A tool that needs third-party software lives under `pdf/` (or a like-named optional folder), lists exact versions in that folder's `requirements.txt`, keeps its tests inside that folder, and has its own CI job; the core's jobs never install anything.**

## Why

The core's promise that it needs nothing else to install stays true.

Two PDF tools that already existed need pypdf, reportlab and poppler. They are
added here as optional tools, so the software they need is listed in one place
and the core stays free of it.

The `pdf-tests` job runs on macOS, because md-table-pdf needs a macOS font and
the tests expect poppler at `/opt/homebrew/bin`.

Known follow-ups: (1) The pins are plain, not hashed: a later change can move to
`pip install --require-hashes`. (2) Homebrew's poppler cannot be pinned the way
the pip packages are. A new poppler release can change the pixels page-render
renders or the text its checks compare, so the `pdf-tests` job can start
failing, or results can shift, with no change in this repository.
