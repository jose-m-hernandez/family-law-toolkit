# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Synthetic fixtures (invented names and text only)."""
import os

LONG = ("The Harbor Lantern Cooperative ledger records that " +
        " ".join("entry%03d describes an invented shipment of brass whistles" % i
                  for i in range(14)) + " END-OF-LONG-CELL.")
assert len(LONG) > 600


def simple():
    return ("# Exhibit A\n\nIntro paragraph about the Willow Creek Exhibit.\n\n"
            "| Item | Qty | Note |\n|---|---|---|\n"
            "| Brass whistle | 4 | **fragile** item |\n"
            "| Copper `kettle` | 2 | ships Monday |\n")


def long_cell():
    return "| Id | Narrative |\n|---|---|\n| 1 | %s |\n| 2 | short |\n" % LONG


def many_rows(n=130):
    out = ["# Ledger", "", "| No | Vessel | Remark |", "|:--|--|--:|"]
    for i in range(n):
        out.append("| R%04d | Vessel Alder-%d | remark uniq%04d for row %d |" % (i, i, i, i))
    return "\n".join(out) + "\n"


def ragged():
    return "| A | B | C |\n|---|---|---|\n| 1 | 2 | 3 |\n| 4 | 5 |\n"


def no_table():
    return "# Just text\n\nNo tables here | but a pipe.\n"


def escaped_pipes():
    return "| Expr | Meaning |\n|---|---|\n| a \\| b | either a or b |\n"


def non_ascii():
    return ("| Nombre | Cita |\n|---|---|\n"
            "| Zoë Núñez | café “quoted” — naïve façade |\n")


def unsupported():
    return "| A | B |\n|---|---|\n| \U0001F600 | x |\n"


def sections(rows=(15, 5, 4), words=25):
    """H1, subtitle paragraph, then one H2 + table per entry of `rows` (r2 layout fixture)."""
    out = ["# Matter Summary", "",
           "Subtitle paragraph for the invented Harbor Lantern matter, prepared for review.", ""]
    k = 0
    for s, n in enumerate(rows, 1):
        out += ["## Section %d" % s, "", "| Date | Event | Note |", "|---|---|---|"]
        for _ in range(n):
            k += 1
            out.append("| 3/%02d/2031 | Event %d | %s |"
                       % (k, k, " ".join("word%d" % j for j in range(words))))
        out.append("")
    return "\n".join(out)


def two_sections(n1, n2):
    """H1, then two H2 sections: n1 short rows, n2 short rows (r2 heading-at-bottom fixture)."""
    out = ["# Doc", "", "## First", "", "| A | B |", "|---|---|"]
    out += ["| a%d | b%d |" % (i, i) for i in range(n1)]
    out += ["", "## Second", "", "| A | B |", "|---|---|"]
    out += ["| c%d | d%d |" % (i, i) for i in range(n2)]
    return "\n".join(out) + "\n"


DATE_TOKENS = ["3/05/2031", "12/22/2031", "3/05-12/22", "12/04-12/22",
               "4/07/2031", "12/31/2031", "4/07-4/09", "12/01-12/31"]  # M/DD/YYYY, MM/DD/YYYY, M/DD-MM/DD, MM/DD-MM/DD


def narrow_dates():
    """A narrow first column of dates beside three wide text columns (r2 mid-token wrap fixture)."""
    filler = " ".join("clause%d of the invented lantern agreement" % i for i in range(8))
    out = ["| Date | Item | Detail | Remark |", "|---|---|---|---|"]
    for d in DATE_TOKENS:
        out.append("| %s | %s | %s | %s |" % (d, filler, filler, filler))
    return "\n".join(out) + "\n"


def write(d, name, text):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p
