"""Command line: python3 -m family_law_toolkit.support --a-ndi ... (five flags required, one optional)."""

import argparse
import sys

from family_law_toolkit.support.guideline import compute
from family_law_toolkit.support.report import render_report


_FLAG_FOR_NAME = {
    "a_ndi": "--a-ndi",
    "b_ndi": "--b-ndi",
    "a_time_percent": "--a-time-percent",
    "children": "--children",
    "minimum_wage_hourly": "--minimum-wage-hourly",
    "same_time_sharing_arrangement": "--same-time-sharing-arrangement",
}


_HELP_TEXT = """\
usage: python3 -m family_law_toolkit.support --a-ndi AMOUNT --b-ndi AMOUNT
       --a-time-percent PERCENT --children COUNT
       --minimum-wage-hourly AMOUNT [--same-time-sharing-arrangement yes|no]

Guideline child support (California Family Code section 4055)
Educational; not legal advice; not certified for court filing; consult counsel.

Required:
  --a-ndi AMOUNT
      Parent A net disposable income
  --b-ndi AMOUNT
      Parent B net disposable income
  --a-time-percent PERCENT
      Parent A's share of time
  --children COUNT
      Number of children
  --minimum-wage-hourly AMOUNT
      Hourly state minimum wage used (Lab. Code 1182.12)
Optional:
  --same-time-sharing-arrangement yes|no
      All children share one time-sharing arrangement
      It has an effect only with two or more children.

Write AMOUNT and PERCENT as plain numbers with at most two decimals, such as
6919.09: no commas, no dollar sign. PERCENT is from 0 to 100. COUNT is a whole
number from 1 to 10.
Net disposable income amounts are monthly dollars; the minimum wage is per
hour.
Parent A and Parent B are labels for the two parents. Use the same labels for
every input.
You enter net disposable income yourself. This version does not work it out
from deductions (FC 4059).
You enter the share of time yourself. The default-proceeding rule (FC
4055(b)(6)) is not applied.
The per-child allocation (FC 4055(b)(8)) is shown only if you add
--same-time-sharing-arrangement yes. It does not apply when the children have
different time-sharing arrangements.

Example, with invented numbers:
    python3 -m family_law_toolkit.support --a-ndi 6919.09 --b-ndi 2255.71 --a-time-percent 35 --children 2 --minimum-wage-hourly 21.00"""


class _OneLineParser(argparse.ArgumentParser):
    """Report any usage problem as one line on stderr and exit 2."""

    def error(self, message):
        sys.stderr.write(
            "%s: error: %s. Run with --help to see what each flag means.\n"
            % (self.prog, message)
        )
        raise SystemExit(2)


def _build_parser():
    parser = _OneLineParser(
        prog="python3 -m family_law_toolkit.support",
        allow_abbrev=False,
        add_help=False,
    )
    parser.add_argument("--a-ndi", required=True)
    parser.add_argument("--b-ndi", required=True)
    parser.add_argument("--a-time-percent", required=True)
    parser.add_argument("--children", required=True, type=int)
    parser.add_argument("--minimum-wage-hourly", required=True)
    parser.add_argument(
        "--same-time-sharing-arrangement", choices=["yes", "no"], required=False
    )
    return parser


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else list(argv)
    if "-h" in arguments or "--help" in arguments:
        sys.stdout.write(_HELP_TEXT + "\n")
        return 0
    args = _build_parser().parse_args(argv)
    try:
        result = compute(
            args.a_ndi,
            args.b_ndi,
            args.a_time_percent,
            args.children,
            args.minimum_wage_hourly,
            args.same_time_sharing_arrangement,
        )
    except ValueError as error:
        name, space, rest = str(error).partition(" ")
        message = _FLAG_FOR_NAME.get(name, name) + space + rest
        sys.stderr.write("python3 -m family_law_toolkit.support: error: %s\n" % message)
        return 2
    sys.stdout.write(render_report(result) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
