# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Command line: python3 -m family_law_toolkit.compare --old FILE --new FILE."""

import argparse
import errno
import os
import stat
import sys

from family_law_toolkit.compare import differences, report

_PROG = "python3 -m family_law_toolkit.compare"
_USAGE_END = ". Run with --help to see what each flag means."
_NOT_PLAIN = "is not a plain-text file; this version reads plain text and Markdown only"
_REFUSED_SUFFIXES = (".pdf", ".docx", ".doc", ".rtf", ".odt")
_REFUSED_MESSAGES = {
    "not-plain-text": _NOT_PLAIN,
    "not-utf-8": "cannot be read as UTF-8",
    "no-text": "has no text to compare",
}

_HELP_TEXT = """\
usage: python3 -m family_law_toolkit.compare --old FILE --new FILE

Compare the text of two files.
Educational; not legal advice; not certified for court filing; consult counsel.

Required:
  --old FILE
      One file: plain text or Markdown
  --new FILE
      The other file: plain text or Markdown

Each file is read as UTF-8 text, up to 200,000 bytes. PDF and Word files are
not read. "Old" and "new" are your labels; this tool does not check which file
is older.
It lists differences in the text. It does not say whether any difference
matters.
The report is not a certified comparison and is not a court record.

Exit status: 0 the files are identical byte for byte, 1 they differ, 2 the
comparison could not run."""


class _Failure(Exception):
    """A case from spec section 7; the text is the message, not yet escaped."""


class _WriteFailure(Exception):
    pass


class _OneLineParser(argparse.ArgumentParser):
    """Report any usage problem as one line on stderr and exit 2."""

    def error(self, message):
        raise _Failure(message + _USAGE_END)


def _build_parser():
    parser = _OneLineParser(prog=_PROG, allow_abbrev=False, add_help=False)
    parser.add_argument("--old", required=True, action="append")
    parser.add_argument("--new", required=True, action="append")
    return parser


def _write(name, data):
    """Write bytes to sys.<name>.buffer, looked up now, in one call."""
    try:
        buffer = getattr(sys, name).buffer
        buffer.write(data)
        buffer.flush()
    except Exception:
        if name == "stdout":
            try:  # keep Python from failing again when it flushes at exit
                os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
            except Exception:
                pass
        raise _WriteFailure() from None


def _reason(error):
    if error.errno in (errno.ENOENT, errno.ENOTDIR):
        return "no such file"
    if error.errno in (errno.EACCES, errno.EPERM):
        return "permission denied"
    return "it could not be read"


def _read(option, path):
    """Section 7 rows 2 to 4 for one file."""
    try:
        mode = os.stat(path).st_mode
    except OSError as error:
        raise _Failure("cannot read %s %s: %s" % (option, path, _reason(error))) from None
    if stat.S_ISDIR(mode):
        raise _Failure("cannot read %s %s: it is a folder" % (option, path))
    if not stat.S_ISREG(mode):
        raise _Failure("cannot read %s %s: it is not a regular file" % (option, path))
    try:
        with open(path, "rb") as handle:
            data = handle.read(differences.MAX_BYTES + 1)
    except OSError as error:
        raise _Failure("cannot read %s %s: %s" % (option, path, _reason(error))) from None
    if len(data) > differences.MAX_BYTES:
        raise _Failure("%s %s is larger than 200,000 bytes" % (option, path))
    if path.lower().endswith(_REFUSED_SUFFIXES):
        raise _Failure("%s %s %s" % (option, path, _NOT_PLAIN))
    return data


def _run(arguments):
    args = _build_parser().parse_args(arguments)
    paths = {}
    for name in ("old", "new"):
        values = getattr(args, name)
        if len(values) > 1:
            raise _Failure("--%s was given more than once%s" % (name, _USAGE_END))
        if values[0] == "-":
            raise _Failure("--%s cannot be -%s" % (name, _USAGE_END))
        paths[name] = values[0]
    data = {name: _read("--" + name, paths[name]) for name in ("old", "new")}
    if os.path.samefile(paths["old"], paths["new"]):
        raise _Failure("--old and --new name the same file")
    for name in ("old", "new"):
        try:
            differences.check(data[name])
        except differences.Refused as refused:
            raise _Failure("--%s %s %s" % (name, paths[name], _REFUSED_MESSAGES[refused.reason])) from None
    try:
        result = differences.compare(data["old"], data["new"])
    except differences.TooManyParagraphs:
        raise _Failure(
            "too many paragraphs lie between the first and last differences to compare "
            "within this tool's limit"
        ) from None
    text = report.render_report(result, paths["old"], paths["new"])
    _write("stdout", text.encode("utf-8"))
    return 0 if result.identical else 1


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else list(argv)
    try:
        if "-h" in arguments or "--help" in arguments:
            _write("stdout", (_HELP_TEXT + "\n").encode("utf-8"))
            return 0
        return _run(arguments)
    except _Failure as failure:
        message = str(failure)
    except _WriteFailure:
        message = "cannot write output"
    except Exception:
        message = "internal error; the comparison did not finish"
    line = report.escape("%s: error: %s" % (_PROG, message), space=True) + "\n"
    try:
        _write("stderr", line.encode("utf-8"))
    except _WriteFailure:
        pass
    return 2


if __name__ == "__main__":
    sys.exit(main())
