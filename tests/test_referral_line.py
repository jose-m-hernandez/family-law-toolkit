"""The referral sentence appears once in the README and once in --help."""

import re
import unittest
from pathlib import Path

from tests.test_report import run_cli

ROOT = Path(__file__).resolve().parent.parent
R1 = (
    "For help working out the figures for your own case, you can ask a lawyer, "
    "your court's self-help center, or its family law facilitator."
)


class ReferralLineTests(unittest.TestCase):
    def test_readme_has_the_referral_line_once(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(text.splitlines().count(R1), 1)
        self.assertEqual(text.count(R1), 1)

    def test_help_has_the_referral_line_once(self):
        done = run_cli("--help")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(re.sub(r"\s+", " ", done.stdout).count(R1), 1)


if __name__ == "__main__":
    unittest.main()
