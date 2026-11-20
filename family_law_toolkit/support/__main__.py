# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Command line: python3 -m family_law_toolkit.support --a-ndi ... (five flags required, six optional)."""

import argparse
import dataclasses
import sys

from family_law_toolkit.support.additional import (
    AdditionalSupportRefused,
    compute_additional,
)
from family_law_toolkit.support.guideline import (
    _parse_amount,
    _parse_percent,
    compute,
)
from family_law_toolkit.support.report import render_report


_FLAG_FOR_NAME = {
    "a_ndi": "--a-ndi",
    "b_ndi": "--b-ndi",
    "a_time_percent": "--a-time-percent",
    "children": "--children",
    "minimum_wage_hourly": "--minimum-wage-hourly",
    "same_time_sharing_arrangement": "--same-time-sharing-arrangement",
    "childcare_monthly": "--childcare-monthly",
    "uninsured_health_monthly": "--uninsured-health-monthly",
    "a_adjusted_ndi": "--a-adjusted-ndi",
    "b_adjusted_ndi": "--b-adjusted-ndi",
    "a_cost_share_percent": "--a-cost-share-percent",
}

# The new options, in the order their values are checked. The first four are
# amounts; the last is a percent.
_NEW_AMOUNTS = (
    "childcare_monthly",
    "uninsured_health_monthly",
    "a_adjusted_ndi",
    "b_adjusted_ndi",
)
_NEW_PERCENT = "a_cost_share_percent"
_NEW_ORDER = _NEW_AMOUNTS + (_NEW_PERCENT,)

# Shown in the refusals that ask for the income figures (spec 3.3).
E3 = (
    "If no spousal support is or has been ordered, enter the same figures you "
    "gave for `--a-ndi` and `--b-ndi`."
)


_HELP_TEXT = """\
usage: python3 -m family_law_toolkit.support --a-ndi AMOUNT --b-ndi AMOUNT
       --a-time-percent PERCENT --children COUNT
       --minimum-wage-hourly AMOUNT [--same-time-sharing-arrangement yes|no]
       [--childcare-monthly AMOUNT] [--uninsured-health-monthly AMOUNT]
       [--a-adjusted-ndi AMOUNT --b-adjusted-ndi AMOUNT]
       [--a-cost-share-percent PERCENT]

Guideline child support (California Family Code section 4055)
Educational; not legal advice; not certified for court filing; consult counsel.

Required:
  --a-ndi AMOUNT
      Parent A net disposable income
  --b-ndi AMOUNT
      Parent B net disposable income
  --a-time-percent PERCENT
      Parent A's share of time
      Repeat the flag once per child to enter a share for each child.
  --children COUNT
      Number of children
  --minimum-wage-hourly AMOUNT
      Hourly state minimum wage used (Lab. Code 1182.12)
Optional:
  --same-time-sharing-arrangement yes|no
      All children share one time-sharing arrangement
      It has an effect only with two or more children.
Additional child support (optional):
  --childcare-monthly AMOUNT
      FC 4062(a)(1) names:
      "Childcare costs, if those expenses are actually incurred, related to
      employment or to reasonably necessary education or training for
      employment skills, as described in Section 4063, unless those costs are
      specifically included in the guideline calculation itself."
  --uninsured-health-monthly AMOUNT
      FC 4062(a)(2) names:
      "The reasonable uninsured health care costs for the children as provided
      in Section 4063."
  --a-adjusted-ndi AMOUNT
      Parent A's net disposable income, after any spousal-support adjustment
      you worked out.
      Not reduced for child support: this report makes the FC 4061(d)
      reduction itself.
      If no spousal support is or has been ordered, enter the same figures you
      gave for `--a-ndi` and `--b-ndi`.
  --b-adjusted-ndi AMOUNT
      Parent B's net disposable income, after any spousal-support adjustment
      you worked out.
      Not reduced for child support: this report makes the FC 4061(d)
      reduction itself.
      If no spousal support is or has been ordered, enter the same figures you
      gave for `--a-ndi` and `--b-ndi`.
  --a-cost-share-percent PERCENT
      Parent A's share of the additional child support costs, as you choose it.
These figures are yours to work out. Cost and income figures are monthly
dollars. Give --a-cost-share-percent, or both --a-adjusted-ndi and
--b-adjusted-ndi, with any cost.

Write AMOUNT and PERCENT as plain numbers with at most two decimals, such as
9500.00: no commas, no dollar sign. PERCENT is from 0 to 100. COUNT is a whole
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
For help working out the figures for your own case, you can ask a lawyer, your
court's self-help center, or its family law facilitator.

Example, with invented numbers:
    python3 -m family_law_toolkit.support --a-ndi 9500.00 --b-ndi 3500.00 --a-time-percent 15 --children 3 --minimum-wage-hourly 21.00

Example with costs, with invented numbers:
    python3 -m family_law_toolkit.support --a-ndi 5000.00 --b-ndi 3000.00 \\
      --a-time-percent 20 --children 1 --minimum-wage-hourly 21.00 \\
      --childcare-monthly 600.00 --uninsured-health-monthly 120.00 \\
      --a-adjusted-ndi 5000.00 --b-adjusted-ndi 3000.00"""


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
    parser.add_argument("--a-time-percent", required=True, action="append")
    parser.add_argument("--children", required=True, type=int)
    parser.add_argument("--minimum-wage-hourly", required=True)
    parser.add_argument(
        "--same-time-sharing-arrangement", choices=["yes", "no"], required=False
    )
    # Additional child support. Each is append, so a repeat can be seen and refused.
    for name in _NEW_ORDER:
        parser.add_argument(
            _FLAG_FOR_NAME[name], dest=name, action="append", required=False
        )
    return parser


def _refuse(message):
    """Print one line to stderr, nothing to stdout; message is a whole sentence."""
    sys.stderr.write(
        "python3 -m family_law_toolkit.support: error: %s "
        "Run with --help to see what each flag means.\n" % message
    )
    return 2


def _parse_new_options(args):
    """Check the five new options. Returns (values, None) or (None, refusal message).

    values maps each option's dest to a Fraction, or to None when not given.
    The order of the checks is fixed so every combination has one message.
    """
    for name in _NEW_ORDER:
        if len(getattr(args, name) or ()) > 1:
            return None, "%s was given more than once." % _FLAG_FOR_NAME[name]
    values = {}
    for name in _NEW_ORDER:
        given = getattr(args, name)
        if given is None:
            values[name] = None
            continue
        parse = _parse_percent if name == _NEW_PERCENT else _parse_amount
        try:
            values[name] = parse(name, given[0])
        except ValueError as error:
            words = str(error).split(" ")
            words[0] = _FLAG_FOR_NAME.get(words[0], words[0])
            return None, " ".join(words) + "."
    return values, None


def _combination_refusal(values):
    """The refusal for a combination of the new options, or None (spec 3.3)."""
    share = values[_NEW_PERCENT]
    a_adjusted = values["a_adjusted_ndi"]
    b_adjusted = values["b_adjusted_ndi"]
    adjusted_given = [
        _FLAG_FOR_NAME[name]
        for name in ("a_adjusted_ndi", "b_adjusted_ndi")
        if values[name] is not None
    ]
    cost_given = (
        values["childcare_monthly"] is not None
        or values["uninsured_health_monthly"] is not None
    )
    if share is not None and adjusted_given:
        return (
            "--a-cost-share-percent was given together with an adjusted-income "
            "option, so it is unclear which split to use. Give one or the other."
        )
    if len(adjusted_given) == 1:
        return (
            "Only %s was given, and this report needs both --a-adjusted-ndi and "
            "--b-adjusted-ndi. %s" % (adjusted_given[0], E3)
        )
    if a_adjusted is not None and b_adjusted is not None and not cost_given:
        return (
            "--a-adjusted-ndi and --b-adjusted-ndi were given with no cost, so "
            "they would go unused. Give --childcare-monthly or "
            "--uninsured-health-monthly, or leave them out."
        )
    if share is not None and not cost_given:
        return (
            "--a-cost-share-percent was given with no cost, so it would go unused. "
            "Give --childcare-monthly or --uninsured-health-monthly, or leave it out."
        )
    if cost_given and share is None and a_adjusted is None:
        return (
            "A cost was entered without a way to split it: give "
            "--a-cost-share-percent, or give both --a-adjusted-ndi and "
            "--b-adjusted-ndi. %s" % E3
        )
    return None


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else list(argv)
    if "-h" in arguments or "--help" in arguments:
        sys.stdout.write(_HELP_TEXT + "\n")
        return 0
    args = _build_parser().parse_args(argv)
    values, refusal = _parse_new_options(args)
    if refusal is None:
        refusal = _combination_refusal(values)
    if refusal is not None:
        return _refuse(refusal)
    # One value is a single share of time; repeating the flag gives one per child.
    shares = args.a_time_percent
    a_time_percent = shares[0] if len(shares) == 1 else shares
    try:
        result = compute(
            args.a_ndi,
            args.b_ndi,
            a_time_percent,
            args.children,
            args.minimum_wage_hourly,
            args.same_time_sharing_arrangement,
        )
    except ValueError as error:
        # A plain ValueError names its parameter in the first word only. An error
        # that names several declares them (error.names); only those words map.
        names = getattr(error, "names", None)
        words = str(error).split(" ")
        if names is None:
            words[0] = _FLAG_FOR_NAME.get(words[0], words[0])
        else:
            words = [_FLAG_FOR_NAME[w] if w in names else w for w in words]
        message = " ".join(words)
        sys.stderr.write("python3 -m family_law_toolkit.support: error: %s\n" % message)
        return 2
    if values["childcare_monthly"] is not None or values["uninsured_health_monthly"] is not None:
        try:
            additional = compute_additional(
                result,
                values["childcare_monthly"],
                values["uninsured_health_monthly"],
                values["a_adjusted_ndi"],
                values["b_adjusted_ndi"],
                values[_NEW_PERCENT],
            )
        except AdditionalSupportRefused as error:
            return _refuse(str(error))
        result = dataclasses.replace(result, additional=additional)
    sys.stdout.write(render_report(result) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
