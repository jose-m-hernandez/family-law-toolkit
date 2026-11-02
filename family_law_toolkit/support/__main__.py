"""Command line: python3 -m family_law_toolkit.support --a-ndi ... (five flags required, one optional)."""

import argparse
import sys

from family_law_toolkit.support.guideline import compute
from family_law_toolkit.support.report import render_report


class _OneLineParser(argparse.ArgumentParser):
    """Report any usage problem as one line on stderr and exit 2."""

    def error(self, message):
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
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
        sys.stderr.write("python3 -m family_law_toolkit.support: error: %s\n" % error)
        return 2
    sys.stdout.write(render_report(result) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
