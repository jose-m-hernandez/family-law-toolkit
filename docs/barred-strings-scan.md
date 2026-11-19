# The barred-strings scan

The scan, `ci/barred_strings.py`, checks every version of every file reachable from the current commit, both contents and file names, along with commit messages, author and committer names and emails, and the branch name. Matching ignores runs of whitespace (a line break, a tab or repeated spaces counts as one space) and invisible format characters such as a soft hyphen or a zero-width space. It runs in CI on every push and pull request, against a private list held in the `BARRED_STRINGS` repository secret. Contributors cannot run it against that list and do not need to; CI runs it for them. It prints entry numbers only, never the matched text. The maintainer can run it locally by keeping a list file outside the repository and running `BARRED_STRINGS_PATH=/path/to/list python3 ci/barred_strings.py`. It reads committed history only, so uncommitted edits are not scanned.

## Exit codes

- 0: clean.
- 1: a hit.
- 2: the scan could not run.

## Try it

To try the scan with an invented list, run this from the repository root. The entries are generated at run time, so nothing in the repository can contain them:

    n=$(date +%s)
    printf 'barred-strings-canary-%s\ntry-%s-qx\n' "$n" "$n" > /tmp/try-list.txt
    BARRED_STRINGS_PATH=/tmp/try-list.txt python3 ci/barred_strings.py; echo "exit $?"
    rm /tmp/try-list.txt

The first line starts `barred-strings scan: clean`, then `exit 0` prints.

To see a hit, make entry 2 a string that is in the README, `Counting fifth weeks`:

    n=$(date +%s)
    printf 'barred-strings-canary-%s\nCounting fifth weeks\n' "$n" > /tmp/try-list.txt
    BARRED_STRINGS_PATH=/tmp/try-list.txt python3 ci/barred_strings.py; echo "exit $?"
    rm /tmp/try-list.txt

The first line starts `entry 2 matched in`, and the last line is `exit 1`. The README contains that string, so the scan finds it.

## The list format

- One entry per line. An entry ends at the first tab, and anything after the tab is a note that is never matched.
- `#` lines and blank lines are ignored.
- Matching is literal and case-insensitive after Unicode NFKC.
- The first entry is a canary: `barred-strings-canary-` plus at least 8 letters or digits.
- Writing `word` (any case, and nothing else in that field) right after an entry's first tab makes the entry match only as a whole word. The canary cannot carry the flag.

A letter or digit on either side prevents a whole-word match; spaces, punctuation, `-`, `_` and the start or end of the text count as boundaries.
