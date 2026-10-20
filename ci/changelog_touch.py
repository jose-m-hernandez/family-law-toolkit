"""Fail a pull request that adds no entry under "## [Unreleased]" in CHANGELOG.md.

Usage: python3 ci/changelog_touch.py --base <rev> [--head <rev>]

It reads committed content only (`git show <rev>:CHANGELOG.md`), never the
working tree, and compares the file at the merge base of --base and --head with
the file at --head.

Rules
-----
* The "## [Unreleased]" section is every line after that heading up to the next
  line starting "## ". An entry is a line matching "- " followed by a
  non-space character.
* Pass when head has more entries than the merge base and at least one entry
  that the merge base lacks (multisets, so a second copy of an existing line
  counts).
* A reword keeps the count, so it fails. A removal shrinks the count, so it
  fails.
* Known fail-closed edge, by design: removing one entry and adding another
  leaves the count unchanged and fails. The author keeps the old line or adds
  a second one.
* Release shape: head has a new "## [X.Y.Z] - YYYY-MM-DD" heading (digits and
  dots only), head's Unreleased section has no entries, and the new release
  section holds exactly the entries the merge base had under Unreleased (and
  at least one). That passes without a new entry.
* Limit, by design: it catches an honest omission and is not an adversarial
  control, so a zero-width or fenced entry, a fenced release heading or a
  re-dated duplicate can pass.

Output is one line of counts, never entry text. Exit codes: 0 pass, 1 fail,
2 anything that could not be checked (it fails closed).
"""

import argparse
import re
import subprocess
import sys
from collections import Counter

PREFIX = "changelog-touch: "
UNRELEASED = "## [Unreleased]"
ENTRY_RE = re.compile(r"^- \S")
RELEASE_RE = re.compile(r"^## \[([0-9]+\.[0-9]+\.[0-9]+)\] - [0-9]{4}-[0-9]{2}-[0-9]{2}[ ]*$")


class Closed(Exception):
    """A condition that fails closed with a specific message (exit 2)."""


def say(msg):
    print(PREFIX + msg)


def git(*args):
    return subprocess.run(
        ["git"] + list(args),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def resolve(rev, label):
    if rev.startswith("-") or not rev:
        raise Closed("cannot resolve %s; failing closed" % label)
    proc = git("rev-parse", "--verify", "--quiet", rev + "^{commit}")
    sha = proc.stdout.decode("ascii", "replace").strip()
    if proc.returncode != 0 or not sha:
        raise Closed("cannot resolve %s; failing closed" % label)
    return sha


def read_changelog(rev, label):
    proc = git("show", "%s:CHANGELOG.md" % rev)
    if proc.returncode != 0:
        raise Closed("CHANGELOG.md missing at %s; failing closed" % label)
    try:
        text = proc.stdout.decode("utf-8")
    except UnicodeDecodeError:
        raise Closed("CHANGELOG.md at %s is not UTF-8; failing closed" % label)
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def section(lines, start):
    out = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        out.append(line)
    return out


def unreleased_section(lines, label):
    idx = [i for i, ln in enumerate(lines) if ln.rstrip(" ") == UNRELEASED
           and ln.startswith(UNRELEASED)]
    if len(idx) != 1:
        raise Closed(
            'expected one "## [Unreleased]" heading at %s, found %d; '
            "failing closed" % (label, len(idx))
        )
    return section(lines, idx[0])


def entries(sec):
    return Counter(ln for ln in sec if ENTRY_RE.match(ln))


def new_release_headings(base_lines, head_lines):
    old = set(base_lines)
    return [(i, RELEASE_RE.match(ln).group(1)) for i, ln in enumerate(head_lines)
            if RELEASE_RE.match(ln) and ln not in old]


def run(args):
    base = resolve(args.base, "base")
    head = resolve(args.head, "head")
    proc = git("merge-base", base, head)
    mb = proc.stdout.decode("ascii", "replace").strip()
    if proc.returncode != 0 or not mb:
        raise Closed("no merge base between --base and --head; failing closed")

    mb_lines = read_changelog(mb, "merge base")
    head_lines = read_changelog(head, "head")
    b = entries(unreleased_section(mb_lines, "merge base"))
    h_sec = unreleased_section(head_lines, "head")
    h = entries(h_sec)

    added = h - b
    if sum(h.values()) > sum(b.values()) and added:
        n = sum(added.values())
        say("ok: %d new Unreleased entr%s" % (n, "y" if n == 1 else "ies"))
        return 0

    fresh = new_release_headings(mb_lines, head_lines)
    if fresh:
        idx, version = fresh[0]
        rel = entries(section(head_lines, idx))
        if len(fresh) == 1 and not h and rel == b and sum(b.values()) > 0:
            n = sum(rel.values())
            say("ok: release %s carries %d entr%s"
                % (version, n, "y" if n == 1 else "ies"))
            return 0
        say("release %s does not carry the Unreleased entries exactly" % version)
        return 1

    say("no new entry under ## [Unreleased]; add one line to CHANGELOG.md")
    return 1


def main(argv):
    parser = argparse.ArgumentParser(prog="changelog_touch.py")
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args(argv)
    try:
        return run(args)
    except Closed as exc:
        say(str(exc))
        return 2
    except Exception as exc:  # fail closed on anything unforeseen
        say("internal error (%s); failing closed" % type(exc).__name__)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
