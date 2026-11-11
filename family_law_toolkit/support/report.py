# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Plain-text report for the guideline result.

Every page starts with the identity line. There is one way to produce report
text, render_report(result), and it takes no option that could change that.
"""

from family_law_toolkit import TOOLKIT_NAME, __version__
from family_law_toolkit.support.guideline import allocation, cents_text, fixed, money, plain

IDENTITY_LINE = (
    TOOLKIT_NAME
    + " v"
    + __version__
    + " — not certified for court filing; not affiliated with DissoMaster or XSpouse"
)
PAGE_LINES = 60
BODY_LINES_PER_PAGE = PAGE_LINES - 2  # the identity line and one blank line

NOTE_NDI = (
    "You enter net disposable income yourself. "
    "This version does not work it out from deductions (FC 4059)."
)
NOTE_TIME_SHARE = (
    "You enter the share of time yourself. "
    "The default-proceeding rule (FC 4055(b)(6)) is not applied."
)
NOTE_PER_CHILD_NO_FLAG = (
    "The per-child allocation (FC 4055(b)(8)) is shown only if you add "
    "--same-time-sharing-arrangement yes. It does not apply when the children "
    "have different time-sharing arrangements."
)
NOTE_PER_CHILD_DIFFERENT = (
    "The per-child allocation (FC 4055(b)(8)) does not apply, because the "
    "children have different time-sharing arrangements."
)
NOTE_PER_CHILD_DIFFERENT_SHARES = "This toolkit reads different percentages of time for different children as different time-sharing arrangements, so the per-child allocation (FC 4055(b)(8)) does not apply."
NOTE_PER_CHILD_NO_PAYER = (
    "Guideline support is 0.00, so there is no amount to allocate per child "
    "(FC 4055(b)(8))."
)
ECHO_SAME_TIME_SHARING = "  All children share one time-sharing arrangement: %s"

ALLOCATION_HEADING = "Allocation per child (FC 4055(b)(8))"
ALLOCATION_UNLESS_LINE = (
    "  The statute uses this allocation unless the court orders otherwise "
    "(FC 4055(b)(8))."
)
ALLOCATION_HOW_LINE = (
    "  Child 1 is the amount of support for 1 child. Child 2 is the amount for 2 "
    "children less the amount for 1 child, and so on. Together they add up to "
    "%s."
)
ALLOCATION_ROUNDING_LINE = (
    "  This toolkit rounds the amount for each number of children to the cent "
    "before taking the differences; FC 4055 does not say how to round."
)
ALLOCATION_ZERO_LINE = (
    "  Where an amount above shows 0.00, the exact amount is above zero but "
    "under one cent. It shows 0.00 because this toolkit rounds the running "
    "totals to the cent before taking the differences. It is not an allocation "
    "of zero support."
)
ALLOCATION_TOP_LINE = "  At the top of the support range (no low-income reduction):"
ALLOCATION_BOTTOM_LINE = (
    "  At the bottom of the support range (the largest permitted reduction):"
)
ALLOCATION_RANGE_LINE = (
    "  The court sets the amount within the range, and FC 4055(b)(8) then "
    "allocates the amount it orders. No allocation is shown for amounts between "
    "the two ends shown."
)
ALLOCATION_REDUCTION_LINE = (
    "  This toolkit applies the largest reduction to the amount for each number "
    "of children; FC 4055(b)(7) does not say that the (b)(8) amounts are adjusted."
)

LOW_INCOME_HEADING = "Low-income adjustment (FC 4055(b)(7); range under FC 4055(c))"
READING_R2_LINE = (
    "  This toolkit reads the monthly threshold as the hourly minimum wage "
    "x 40 x 52 / 12 (FC 4055(b)(7))."
)
READING_AVERAGE_LINE = (
    "  This toolkit reads the average in FC 4055(b)(1)(D) as the high earner's "
    "percentages of time with each child, added up and divided by the number "
    "of children. The formula uses the exact average; H% above is shown "
    "rounded to two decimals."
)
NO_SINGLE_FIGURE_LINE = (
    "  The presumption is rebuttable and no single figure in the range is chosen."
)


def paginate(body_lines):
    """Split body lines into pages; each page opens with the identity line."""
    lines = list(body_lines)
    chunks = [
        lines[start:start + BODY_LINES_PER_PAGE]
        for start in range(0, len(lines), BODY_LINES_PER_PAGE)
    ] or [[]]
    return ["\n".join([IDENTITY_LINE, ""] + chunk) for chunk in chunks]


def _parent(letter):
    return "none" if letter == "none" else "Parent " + letter


def _support_label(result):
    if result.lia.applies:
        # Not an answer: the range below is the output (FC 4055(c)).
        return "Top of the support range, before any low-income reduction (FC 4055(a), (b)(4))"
    return "Support amount (FC 4055(a), (b)(4))"


def _low_income_lines(result):
    lia = result.lia
    lines = [
        LOW_INCOME_HEADING,
        "  Threshold (FC 4055(b)(7)): %s = hourly minimum wage x 40 x 52 / 12"
        % money(lia.threshold),
    ]
    if lia.applies:
        lines += [
            "  The paying parent's net disposable income is less than the threshold: "
            "a rebuttable presumption that the paying parent is entitled to a "
            "low-income adjustment applies (FC 4055(b)(7)).",
            "  Permitted reduction (FC 4055(b)(7), (c)): 0.00 to %s"
            % money(lia.max_reduction),
            "  Support range (FC 4055(c)): %s to %s"
            % (money(lia.range_low), money(lia.range_high)),
            NO_SINGLE_FIGURE_LINE,
            READING_R2_LINE,
        ]
    elif result.payer == "none":
        lines.append(
            "  There is no paying parent, so the low-income adjustment does not apply "
            "(FC 4055(b)(7))."
        )
    else:
        lines.append(
            "  The paying parent's net disposable income is not less than the threshold, "
            "so the low-income adjustment does not apply (FC 4055(b)(7))."
        )
    return lines


def _allocation_end_lines(end, children, total_words):
    """C3, C4 and C5 for one end of the amount."""
    lines = []
    for count, shown in enumerate(end.cumulative, start=1):
        lines.append(
            "  Amount of support for %d %s (FC 4055(b)(4)): %s"
            % (count, "child" if count == 1 else "children", cents_text(shown))
        )
    for position, shown in enumerate(end.per_child, start=1):
        tag = ""
        if position == 1:
            tag = ", youngest"
        if position == children:
            tag = ", oldest"
        lines.append(
            "  Child %d%s (FC 4055(b)(8)): %s" % (position, tag, cents_text(shown))
        )
    lines.append(ALLOCATION_HOW_LINE % total_words)
    return lines


def _allocation_lines(result, shown):
    """The allocation block (strings C and D), for a non-None allocation."""
    lines = [ALLOCATION_HEADING, ALLOCATION_UNLESS_LINE]
    if shown.bottom is None:
        lines += _allocation_end_lines(shown.top, result.children, "the support amount above")
        lines.append(ALLOCATION_ROUNDING_LINE)
    else:
        lines.append(ALLOCATION_TOP_LINE)
        lines += _allocation_end_lines(shown.top, result.children, "that end of the range")
        lines.append(ALLOCATION_BOTTOM_LINE)
        lines += _allocation_end_lines(shown.bottom, result.children, "that end of the range")
        lines += [ALLOCATION_ROUNDING_LINE, ALLOCATION_RANGE_LINE, ALLOCATION_REDUCTION_LINE]
    ends = [shown.top] + ([shown.bottom] if shown.bottom is not None else [])
    if any(amount == 0 for end in ends for amount in end.per_child):
        lines.append(ALLOCATION_ZERO_LINE)
    return lines


def render_report(result):
    """Return the full report text for a GuidelineResult."""
    hn = result.a_ndi if result.high_earner == "A" else result.b_ndi
    arrangement = result.same_time_sharing_arrangement
    echo = result.children >= 2 and arrangement is not None
    shown = allocation(result)
    by_child = result.a_time_percent_by_child
    if by_child is None:
        share_line = "  Parent A's share of time: %s%%" % plain(result.a_time_percent, 2)
    else:
        share_line = "  Parent A's share of time, by child: " + ", ".join(
            plain(share, 2) + "%" for share in by_child
        )
    differ = by_child is not None and any(share != by_child[0] for share in by_child)
    body = [
        "Guideline child support (California Family Code section 4055)",
        "Amounts are monthly dollars, rounded to the nearest cent (halves round up).",
        "",
        "Inputs as given",
        "  Parent A net disposable income: %s" % money(result.a_ndi),
        "  Parent B net disposable income: %s" % money(result.b_ndi),
        share_line,
        "  Number of children: %d" % result.children,
        "  Hourly state minimum wage used (Lab. Code 1182.12): %s" % money(result.minimum_wage_hourly),
    ]
    if echo:
        body.append(ECHO_SAME_TIME_SHARING % arrangement)
    body += [
        "",
        "Formula",
        "  Total net disposable income, TN (FC 4055(b)(1)(E)): %s" % money(result.tn),
        "  High earner (FC 4055(b)(1)(C)): %s" % _parent(result.high_earner),
        "  High earner's share of time, H%% (FC 4055(b)(1)(D)): %s%%"
        % plain(result.h_percent, 2),
    ]
    if by_child is not None:
        body.append(READING_AVERAGE_LINE)
    body += [
        "  K table row (FC 4055(b)(3)): %d" % result.k_row,
        "  K (FC 4055(b)(3)): %s" % fixed(result.k, 6),
        "  HN, the high earner's net disposable income: %s" % money(hn),
        "  Formula result, CS = K[HN - (H%%)(TN)] (FC 4055(a)): %s"
        % money(result.cs_formula),
        "  Children multiplier (FC 4055(b)(4)): %s" % plain(result.multiplier, 3),
        "  CS times multiplier (FC 4055(b)(4)): %s" % money(result.cs_total),
        "  Paying parent (FC 4055(b)(5)): %s" % _parent(result.payer),
        "  %s: %s" % (_support_label(result), money(result.support)),
        "",
    ]
    body += _low_income_lines(result)
    if shown is not None:
        body += [""] + _allocation_lines(result, shown)
    body += ["", NOTE_NDI, NOTE_TIME_SHARE]
    if result.children >= 2:
        if arrangement == "no":
            body.append(NOTE_PER_CHILD_DIFFERENT)
        elif differ:
            body.append(NOTE_PER_CHILD_DIFFERENT_SHARES)
        elif arrangement is None:
            body.append(NOTE_PER_CHILD_NO_FLAG)
        elif shown is None:
            body.append(NOTE_PER_CHILD_NO_PAYER)
    return "\f".join(paginate(body))
