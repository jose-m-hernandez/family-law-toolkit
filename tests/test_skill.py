# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""The calculator skill: one source file, each harness's path wired to it, and
a drift test that fails if a wired path stops matching or the skill names a
command or flag that does not exist.
"""

import importlib
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from family_law_toolkit.support import __main__ as cli_main
from tests.test_report import run_cli

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "skills" / "support-calculator"
SOURCE = SOURCE_DIR / "SKILL.md"
# Each harness reads a repo-level skill from <root>/<dir>/skills/<name>:
# Claude Code from .claude/skills, Codex from .codex/skills (measured on this
# machine; see docs/decisions/2026-11-19-the-calculator-skill-has-one-source-file.md).
WIRED = (
    ".claude/skills/support-calculator",
    ".codex/skills/support-calculator",
)
MODULE_RE = re.compile(r"python3 -m (family_law_toolkit(?:\.[A-Za-z_][A-Za-z0-9_]*)*)")
FLAG_RE = re.compile(r"(?<![A-Za-z0-9-])--[a-z][a-z0-9-]*")
# --help is handled by main() before the parser sees it (the parser has add_help off).
HANDLED_BEFORE_THE_PARSER = {"--help"}


def named_modules(text):
    return sorted(set(MODULE_RE.findall(text)))


def named_flags(text):
    return sorted(set(FLAG_RE.findall(text)))


def known_flags():
    parser = cli_main._build_parser()
    flags = {option for action in parser._actions for option in action.option_strings}
    return flags | HANDLED_BEFORE_THE_PARSER


def missing_names(text):
    """Every command or flag the text names that does not exist."""
    missing = []
    for module in named_modules(text):
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module)
    missing += [flag for flag in named_flags(text) if flag not in known_flags()]
    return missing


def tracked_mode(path):
    """The git mode of a tracked path, or None when it is not tracked."""
    done = subprocess.run(
        ["git", "ls-files", "-s", "--", path],
        cwd=str(ROOT), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, universal_newlines=True, timeout=60,
    )
    if done.returncode != 0 or not done.stdout.strip():
        return None
    return done.stdout.split()[0]


class SkillTests(unittest.TestCase):
    def test_the_source_file_has_its_frontmatter(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        head = text.split("\n---\n", 1)[0].split("\n")
        self.assertIn("name: support-calculator", head)
        descriptions = [l for l in head if l.startswith("description: ") and len(l) > len("description: ")]
        self.assertEqual(len(descriptions), 1)

    def test_there_is_one_source_file(self):
        found = sorted(
            str(p.relative_to(ROOT)) for p in (ROOT / "skills").rglob("*") if p.is_file()
        )
        self.assertEqual(found, ["skills/support-calculator/SKILL.md"])

    def test_each_wired_path_is_tracked_and_resolves_to_the_source(self):
        if shutil.which("git") is None or not (ROOT / ".git").exists():
            self.skipTest("not run: git or the repository metadata is not available here")
        source_bytes = SOURCE.read_bytes()
        for rel in WIRED:
            with self.subTest(path=rel):
                path = ROOT / rel
                mode = tracked_mode(rel)
                self.assertIsNotNone(mode, rel + " is not tracked by git")
                if mode == "120000":
                    self.assertTrue(path.is_symlink())
                    # A relative link that ends at the one source directory.
                    self.assertFalse(os.path.isabs(os.readlink(str(path))))
                    self.assertEqual(path.resolve(), SOURCE_DIR.resolve())
                # A symlink or, if one was unavoidable, a copy: the bytes are the source's.
                self.assertEqual((path / "SKILL.md").read_bytes(), source_bytes)

    def test_every_command_and_flag_the_skill_names_exists(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(named_modules(text), ["family_law_toolkit.support"])
        self.assertEqual(missing_names(text), [])
        # And the flags are not a short list: the skill names every new option.
        for flag in ("--childcare-monthly", "--uninsured-health-monthly",
                     "--a-adjusted-ndi", "--b-adjusted-ndi",
                     "--a-cost-share-percent", "--same-time-sharing-arrangement"):
            self.assertIn(flag, named_flags(text))

    def test_help_is_handled_by_the_command(self):
        done = run_cli("--help")
        self.assertEqual(done.returncode, 0)

    def test_the_check_can_see_a_missing_flag_or_module(self):
        # A positive control: the same check fails on invented names.
        text = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(missing_names(text + "\nAdd --no-such-flag here.\n"), ["--no-such-flag"])
        self.assertEqual(
            missing_names(text + "\npython3 -m family_law_toolkit.nope\n"),
            ["family_law_toolkit.nope"],
        )

    def test_the_skill_text_makes_no_barred_claim(self):
        lowered = SOURCE.read_text(encoding="utf-8").lower()
        # It names these words only to tell the reader never to use them.
        for word in ("court-ready", "accurate", "add-on"):
            self.assertNotIn(word, lowered)


if __name__ == "__main__":
    unittest.main()
