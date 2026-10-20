"""Tests for ci/changelog_touch.py, each against a throwaway git repository."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = str(Path(__file__).resolve().parent.parent / "ci" / "changelog_touch.py")

BASE_TEXT = """# Changelog

## [Unreleased]

### Added

- alpha widget entry
- beta widget entry

## [0.1.0] - 2026-01-01

### Added

- gamma released entry
"""

FAIL_LINE = "changelog-touch: no new entry under ## [Unreleased]; add one line to CHANGELOG.md"
NO_BASE_LINE = "changelog-touch: no merge base between --base and --head; failing closed"


def ok_line(n):
    return "changelog-touch: ok: %d new Unreleased %s" % (n, "entry" if n == 1 else "entries")


class ChangelogTouchTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(
            os.environ, {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = tmp.name
        self.git("init", "-q", "-b", "main")

    # -- helpers ----------------------------------------------------------

    def git(self, *args, check=True):
        proc = subprocess.run(
            ["git", "-C", self.repo] + list(args),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if check:
            self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.decode("utf-8").strip()

    def write(self, name, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        with open(os.path.join(self.repo, name), "wb") as fh:
            fh.write(data)

    def commit(self, msg="c", *extra):
        self.git("add", "-A")
        self.git(
            "-c", "user.name=Test Author", "-c", "user.email=test@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", msg,
            *extra
        )

    def start(self, text=BASE_TEXT):
        """Commit text on main, then switch to a feature branch."""
        self.write("CHANGELOG.md", text)
        self.commit("base")
        self.git("checkout", "-q", "-b", "feat")

    def change(self, text, msg="change"):
        self.write("CHANGELOG.md", text)
        self.commit(msg)

    def run_tool(self, *args):
        proc = subprocess.run(
            [sys.executable, SCRIPT] + list(args),
            cwd=self.repo,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def check(self, rc, line, *args):
        got_rc, out, err = self.run_tool(*(args or ("--base", "main")))
        self.assertEqual(out, line + "\n")
        self.assertEqual(got_rc, rc, err)

    # -- passes -----------------------------------------------------------

    def test_new_entry_under_existing_group_passes(self):
        self.start()
        self.change(BASE_TEXT.replace("- beta widget entry\n", "- beta widget entry\n- delta new entry\n"))
        self.check(0, ok_line(1))

    def test_new_entry_under_new_group_passes(self):
        self.start()
        self.change(BASE_TEXT.replace("\n## [0.1.0]", "\n### Fixed\n\n- epsilon fix entry\n\n## [0.1.0]"))
        self.check(0, ok_line(1))

    def test_two_new_entries_counted(self):
        self.start()
        self.change(BASE_TEXT.replace("- beta widget entry\n", "- beta widget entry\n- delta one\n- zeta two\n"))
        self.check(0, ok_line(2))

    def test_duplicate_of_existing_entry_counts(self):
        self.start()
        self.change(BASE_TEXT.replace("- alpha widget entry\n", "- alpha widget entry\n- alpha widget entry\n"))
        self.check(0, ok_line(1))

    def test_merge_commit_head_passes(self):
        self.start()
        self.change(BASE_TEXT.replace("- beta widget entry\n", "- beta widget entry\n- delta new entry\n"))
        self.git("checkout", "-q", "main")
        self.write("other.txt", "unrelated\n")
        self.commit("main moves on")
        self.git(
            "-c", "user.name=Test Author", "-c", "user.email=test@example.invalid",
            "-c", "commit.gpgsign=false", "merge", "-q", "--no-ff", "-m", "merge", "feat",
        )
        base = self.git("rev-parse", "HEAD~1")
        self.check(0, ok_line(1), "--base", base, "--head", "HEAD")

    def test_crlf_changelog_passes(self):
        crlf = BASE_TEXT.replace("\n", "\r\n")
        self.start(crlf)
        self.change(crlf.replace("- beta widget entry\r\n", "- beta widget entry\r\n- delta new entry\r\n"))
        self.check(0, ok_line(1))

    # -- fails ------------------------------------------------------------

    def test_no_changelog_change_fails(self):
        self.start()
        self.write("other.txt", "x\n")
        self.commit("other")
        self.check(1, FAIL_LINE)

    def test_reword_only_fails(self):
        self.start()
        self.change(BASE_TEXT.replace("alpha widget entry", "alpha widget reworded"))
        self.check(1, FAIL_LINE)

    def test_removal_only_fails(self):
        self.start()
        self.change(BASE_TEXT.replace("- beta widget entry\n", ""))
        self.check(1, FAIL_LINE)

    def test_remove_one_add_one_fails(self):
        self.start()
        self.change(BASE_TEXT.replace("- beta widget entry\n", "- delta new entry\n"))
        self.check(1, FAIL_LINE)

    def test_entry_added_to_released_section_fails(self):
        self.start()
        self.change(BASE_TEXT.replace("- gamma released entry\n", "- gamma released entry\n- late addition\n"))
        self.check(1, FAIL_LINE)

    def test_heading_or_blank_only_fails(self):
        self.start()
        self.change(BASE_TEXT.replace("\n## [0.1.0]", "\n### Fixed\n\n\n## [0.1.0]"))
        self.check(1, FAIL_LINE)

    def test_dash_without_content_fails(self):
        self.start()
        self.change(BASE_TEXT.replace("- beta widget entry\n", "- beta widget entry\n-    \n"))
        self.check(1, FAIL_LINE)

    def test_working_tree_ignored(self):
        self.start()
        self.write("CHANGELOG.md", BASE_TEXT.replace("- beta widget entry\n", "- beta widget entry\n- uncommitted\n"))
        self.check(1, FAIL_LINE)

    # -- fail closed (exit 2) ---------------------------------------------

    def test_no_merge_base_fails_closed(self):
        self.start()
        self.git("checkout", "-q", "--orphan", "other")
        self.commit("orphan root")
        self.git("checkout", "-q", "feat")
        self.check(2, NO_BASE_LINE, "--base", "other")

    def test_bad_rev_fails_closed(self):
        self.start()
        self.check(2, "changelog-touch: cannot resolve base; failing closed", "--base", "deadbeef")

    def test_missing_base_arg_exits_2(self):
        self.start()
        rc, out, err = self.run_tool()
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertIn("--base", err)

    def test_changelog_missing_at_head_fails_closed(self):
        self.start()
        os.remove(os.path.join(self.repo, "CHANGELOG.md"))
        self.commit("delete")
        self.check(2, "changelog-touch: CHANGELOG.md missing at head; failing closed")

    def test_no_unreleased_heading_fails_closed(self):
        self.start()
        self.change(BASE_TEXT.replace("## [Unreleased]", "## [Next]"))
        self.check(
            2,
            'changelog-touch: expected one "## [Unreleased]" heading at head, found 0; failing closed',
        )

    def test_two_unreleased_headings_fail_closed(self):
        self.start()
        self.change(BASE_TEXT + "\n## [Unreleased]\n\n- stray\n")
        self.check(
            2,
            'changelog-touch: expected one "## [Unreleased]" heading at head, found 2; failing closed',
        )

    def test_non_utf8_fails_closed(self):
        self.start()
        self.change(BASE_TEXT.encode("utf-8") + b"\xff\xfe\n")
        self.check(2, "changelog-touch: CHANGELOG.md at head is not UTF-8; failing closed")

    # -- release shape ----------------------------------------------------

    RELEASED = BASE_TEXT.replace(
        "## [Unreleased]\n\n### Added\n\n- alpha widget entry\n- beta widget entry\n",
        "## [Unreleased]\n\n## [0.2.0] - 2026-10-20\n\n### Added\n\n- alpha widget entry\n- beta widget entry\n",
    )

    def test_release_shape_passes(self):
        self.start()
        self.change(self.RELEASED)
        self.check(0, "changelog-touch: ok: release 0.2.0 carries 2 entries")

    def test_release_dropping_an_entry_fails(self):
        self.start()
        self.change(self.RELEASED.replace("- beta widget entry\n", ""))
        self.check(
            1, "changelog-touch: release 0.2.0 does not carry the Unreleased entries exactly"
        )

    def test_release_keeping_unreleased_entries_fails(self):
        self.start()
        self.change(BASE_TEXT.replace(
            "\n## [0.1.0]",
            "\n## [0.2.0] - 2026-10-20\n\n### Added\n\n- alpha widget entry\n- beta widget entry\n\n## [0.1.0]",
        ))
        self.check(
            1, "changelog-touch: release 0.2.0 does not carry the Unreleased entries exactly"
        )

    def test_empty_release_fails(self):
        empty_unreleased = BASE_TEXT.replace(
            "### Added\n\n- alpha widget entry\n- beta widget entry\n\n", ""
        )
        self.start(empty_unreleased)
        self.change(empty_unreleased.replace("\n## [0.1.0]", "\n## [0.2.0] - 2026-10-20\n\n## [0.1.0]"))
        self.check(
            1, "changelog-touch: release 0.2.0 does not carry the Unreleased entries exactly"
        )

    def test_release_heading_with_non_ascii_digit_is_not_a_release(self):
        self.start()
        # U+0661 is the Arabic-Indic digit one: not a release heading.
        self.change(self.RELEASED.replace("[0.2.0]", "[١.2.0]"))
        self.check(1, FAIL_LINE)

    def merge_ref_after_base_advanced(self, feat_changes_changelog):
        """Build a pull_request-style merge commit M on a branch from an advanced main.

        Returns X, the base commit feat forked from. M's first parent is the
        advanced main tip, which carries someone else's Unreleased entry.
        """
        self.start()
        x = self.git("rev-parse", "HEAD")
        if feat_changes_changelog:
            # Added above alpha so the merge with main's entry (below beta) is clean.
            self.change(BASE_TEXT.replace("- alpha widget entry\n", "- feat own entry\n- alpha widget entry\n"))
        else:
            self.write("other.txt", "unrelated\n")
            self.commit("feat touches another file")
        self.git("checkout", "-q", "main")
        self.change(BASE_TEXT.replace("- beta widget entry\n", "- beta widget entry\n- someone else entry\n"))
        self.git("checkout", "-q", "-b", "merge-ref")
        self.git(
            "-c", "user.name=Test Author", "-c", "user.email=test@example.invalid",
            "-c", "commit.gpgsign=false", "merge", "-q", "--no-ff", "-m", "merge", "feat",
        )
        return x

    def test_base_advanced_merge_ref_without_entry_fails(self):
        x = self.merge_ref_after_base_advanced(False)
        self.check(1, FAIL_LINE, "--base", "HEAD^1", "--head", "HEAD")
        # A stale base (the pre-advance commit) gives a false pass: why CI uses HEAD^1.
        self.check(0, ok_line(1), "--base", x, "--head", "HEAD")

    def test_base_advanced_merge_ref_with_entry_passes(self):
        self.merge_ref_after_base_advanced(True)
        self.check(0, ok_line(1), "--base", "HEAD^1", "--head", "HEAD")

    def test_merge_base_not_base_tip_is_compared(self):
        self.start()
        self.change(BASE_TEXT.replace("- beta widget entry\n", "- beta widget entry\n- feat own entry\n"))
        self.git("checkout", "-q", "main")
        self.change(BASE_TEXT.replace("- beta widget entry\n", "- beta widget entry\n- someone else entry\n"))
        self.git("checkout", "-q", "feat")
        self.check(0, ok_line(1), "--base", "main", "--head", "feat")

    def test_two_new_release_headings_mismatch(self):
        self.start()
        self.change(BASE_TEXT.replace(
            "## [Unreleased]\n\n### Added\n\n- alpha widget entry\n- beta widget entry\n",
            "## [Unreleased]\n\n"
            "## [0.3.0] - 2026-10-21\n\n### Added\n\n- beta widget entry\n\n"
            "## [0.2.0] - 2026-10-20\n\n### Added\n\n- alpha widget entry\n",
        ))
        self.check(
            1, "changelog-touch: release 0.3.0 does not carry the Unreleased entries exactly"
        )

    def test_rev_starting_with_dash_fails_closed(self):
        self.start()
        self.check(2, "changelog-touch: cannot resolve base; failing closed", "--base=--output=x")
        self.assertFalse(os.path.exists(os.path.join(self.repo, "x")))

    def test_second_new_release_heading_is_a_mismatch_even_when_the_first_carries_all(self):
        self.start()
        self.change(BASE_TEXT.replace(
            "## [Unreleased]\n\n### Added\n\n- alpha widget entry\n- beta widget entry\n",
            "## [Unreleased]\n\n"
            "## [0.3.0] - 2026-10-21\n\n### Added\n\n- alpha widget entry\n- beta widget entry\n\n"
            "## [0.2.0] - 2026-10-20\n",
        ))
        self.check(
            1, "changelog-touch: release 0.3.0 does not carry the Unreleased entries exactly"
        )

    def test_dash_rev_is_refused_before_git_runs(self):
        from ci import changelog_touch
        import contextlib
        import io

        buf = io.StringIO()
        with mock.patch.object(
            changelog_touch, "git", side_effect=AssertionError("git called")
        ) as fake_git, contextlib.redirect_stdout(buf):
            rc = changelog_touch.main(["--base=-x"])
        self.assertEqual(rc, 2)
        self.assertEqual(buf.getvalue(), "changelog-touch: cannot resolve base; failing closed\n")
        fake_git.assert_not_called()

    def test_unreleased_heading_with_trailing_spaces_is_found(self):
        text = BASE_TEXT.replace("## [Unreleased]\n", "## [Unreleased]   \n")
        self.start(text)
        self.change(text.replace("- beta widget entry\n", "- beta widget entry\n- delta new entry\n"))
        self.check(0, ok_line(1))

    def test_release_heading_with_trailing_spaces_counts(self):
        self.start()
        self.change(self.RELEASED.replace("## [0.2.0] - 2026-10-20\n", "## [0.2.0] - 2026-10-20   \n"))
        self.check(0, "changelog-touch: ok: release 0.2.0 carries 2 entries")

    def test_dash_tab_line_is_not_an_entry(self):
        self.start()
        self.change(BASE_TEXT.replace("- beta widget entry\n", "- beta widget entry\n-\tdelta tab line\n"))
        self.check(1, FAIL_LINE)

    def test_nested_bullet_is_not_an_entry(self):
        self.start()
        self.change(BASE_TEXT.replace("- beta widget entry\n", "- beta widget entry\n  - delta nested line\n"))
        self.check(1, FAIL_LINE)

    def test_release_must_carry_repeated_entries_as_many_times(self):
        self.start(BASE_TEXT.replace("- alpha widget entry\n", "- alpha widget entry\n- alpha widget entry\n"))
        self.change(self.RELEASED)
        self.check(1, "changelog-touch: release 0.2.0 does not carry the Unreleased entries exactly")

    def test_unexpected_error_fails_closed_with_one_line(self):
        from ci import changelog_touch
        import contextlib
        import io

        buf = io.StringIO()
        with mock.patch.object(
            changelog_touch, "run", side_effect=RuntimeError("boom")
        ), contextlib.redirect_stdout(buf):
            rc = changelog_touch.main(["--base", "main"])
        self.assertEqual(rc, 2)
        self.assertEqual(buf.getvalue(), "changelog-touch: internal error (RuntimeError); failing closed\n")

    # -- privacy ----------------------------------------------------------

    def test_output_never_contains_entry_text(self):
        token = "qzx9uniquetoken"
        self.start(BASE_TEXT.replace("beta widget entry", "beta " + token))
        self.change(
            BASE_TEXT.replace("beta widget entry", "beta " + token)
            .replace("- alpha widget entry\n", "- alpha widget entry\n- new " + token + "\n")
        )
        rc, out, err = self.run_tool("--base", "main")
        self.assertEqual(rc, 0)
        self.assertNotIn(token, out + err)
        self.change(BASE_TEXT.replace("beta widget entry", "beta " + token))
        rc, out, err = self.run_tool("--base", "main")
        self.assertEqual(rc, 1)
        self.assertNotIn(token, out + err)


if __name__ == "__main__":
    unittest.main()
