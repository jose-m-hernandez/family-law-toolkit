# Every push and pull request runs the barred-strings scan

Date: 2026-10-19

## The rule

> **Every push and every pull request runs the barred-strings scan. A failure
> blocks the change. If the scan cannot run, it fails. It prints entry numbers
> only. The list lives only in the repository's `BARRED_STRINGS` secret, never
> in the repository.**

## Why

This repository is private today and will be public, so it is treated as
published from its first commit. A string that must not appear in it cannot
be written down in it either, because naming the string would publish it. So
the list is kept as a secret, and a scan checks every version of every file
reachable from the current commit (contents and file names), plus commit
messages, author and committer names and emails, and the branch name, against it.

What this gate does not check: tags and other branches. The
full-history audit before the repository is published covers them.

The scan must never pass by accident. It fails instead of passing if:

- there is no list;
- the clone is shallow;
- a file cannot be read;
- anything inside the scan goes wrong.

No environment setting or flag makes it pass without the list. Pull requests
from forks get no secrets, so they fail with a plain message rather than being
skipped.

The first entry in the list must be a canary. Before it scans anything, the
scan has to find that canary in a temporary file, so a list that failed to load
cannot produce a clean result.

The scan prints the number of each entry that matched and where, never the
matched text. It posts no comments, annotations or summaries, because those
would copy the match into a place that cannot be taken back.

The alternative, a list kept in the repository or a scan that skips when the
list is missing, was rejected: the first publishes what it guards, and the
second turns a missing secret into a silent pass. The cost is that forks and
local runs need a list supplied from outside the repository.
