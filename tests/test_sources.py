"""Tests that pin the committed text of California Family Code section 4055."""

import hashlib
import html
import re
import unittest
from pathlib import Path

SOURCES = Path(__file__).resolve().parent.parent / "docs" / "sources"
XML_PATH = SOURCES / "fc4055.xml"
TXT_PATH = SOURCES / "fc4055.txt"
XML_SHA256 = "63803b8acd6555bc395704bec61ebcbc1a8b7556e0a2a783e12e2f0253e8a463"
TXT_SHA256 = "aa644b4255702ff9f542648a835da29cd26da468d7a2748f62153870cde9b998"


def sha256_of(path):
    with open(str(path), "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def convert(xml_path):
    """The conversion the fetch used: closing </p> to a line break, tags removed,
    entities decoded, spaces around line breaks trimmed."""
    t = open(str(xml_path), encoding="utf-8").read()
    t = re.sub(r"</p>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[ \t]*\n[ \t]*", "\n", html.unescape(t))
    return t


class SourcesTests(unittest.TestCase):
    def test_xml_hash(self):
        self.assertEqual(sha256_of(XML_PATH), XML_SHA256)

    def test_txt_hash(self):
        self.assertEqual(sha256_of(TXT_PATH), TXT_SHA256)

    def test_txt_has_52_lines(self):
        with open(str(TXT_PATH), "rb") as handle:
            data = handle.read()
        self.assertEqual(data.count(b"\n"), 52)

    def test_txt_is_the_conversion_of_the_xml(self):
        with open(str(TXT_PATH), "rb") as handle:
            txt = handle.read()
        self.assertEqual(txt, convert(XML_PATH).encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
