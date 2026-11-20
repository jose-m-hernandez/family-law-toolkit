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
CLOSING_LINE = (
    "This report is arithmetic on the figures you entered. It is not legal advice."
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

# Additional child support (FC 4062, 4061). Wording is unsigned until reviewed.
ADDITIONAL_REST_HEADING = "Additional child support (FC 4062)"
ADDITIONAL_REST_LINE = (
    "  No additional child support costs were entered. "
    "This report does not say that none apply."
)
ADDITIONAL_HEADING = "Additional child support (FC 4062), split under FC 4061"
ADDITIONAL_COSTS_LINE = "  Costs you entered, monthly:"
ADDITIONAL_CHILDCARE_LABEL = (
    "    Childcare costs related to employment or to reasonably necessary "
    "education or training for employment skills (FC 4062(a)(1)): %s"
)
ADDITIONAL_HEALTH_LABEL = (
    "    The reasonable uninsured health care costs for the children "
    "(FC 4062(a)(2)): %s"
)
ADDITIONAL_NOT_ENTERED = "(not entered)"
ADDITIONAL_TOTAL_LINE = "    Total: %s"
ADDITIONAL_FIGURES_LINE = (
    "  Net disposable income figures used (you entered them; "
    "this report did not adjust them):"
)
ADDITIONAL_A_TYPED_LINE = "    Parent A, as you entered it: %s"
ADDITIONAL_B_TYPED_LINE = "    Parent B, as you entered it: %s"
ADDITIONAL_REDUCTION_HEADING = (
    "  Basic support is taken first (FC 4061(b)(1)); then the paying parent's "
    "figure is reduced by it (FC 4061(d)):"
)
ADDITIONAL_PAYER_LINE = (
    "    Parent %s, the paying parent in this report: %s - %s = %s"
)
ADDITIONAL_NOT_INCREASED_LINE = (
    "    Parent %s is not increased by support received: %s"
)
ADDITIONAL_ZERO_SUPPORT_LINE = (
    "    Basic support prints 0.00, so the reduction is 0.00 and both figures "
    "stay as typed (FC 4061(d))."
)
ADDITIONAL_SPLIT_HEADING = "  Split in proportion to those figures (FC 4061(a), (b)(2)):"
ADDITIONAL_SPLIT_LINE = "    Parent %s: %s / %s = %s%%: %s"
ADDITIONAL_CHOSEN_LINE = "  Split you entered: Parent A %s%%, Parent B %s%%"
ADDITIONAL_CHOSEN_AMOUNT_LINE = "    Parent %s: %s"
ADDITIONAL_TOP_LINE = "  At the top of the support range, %s:"
ADDITIONAL_BOTTOM_LINE = "  At the bottom of the support range, %s:"

NOTE_ADDITIONAL_INCOME = (
    "You enter each parent's adjusted net disposable income yourself. "
    "This report does not adjust income for spousal support (FC 4061(c))."
)
NOTE_ADDITIONAL_MAY = (
    "Costs the court may order (FC 4062(b)) are not computed here, and nothing "
    "in this report shows them as owed."
)
NOTE_ADDITIONAL_DECIDE = (
    "This report does not decide which costs count, whether a cost is actually "
    "incurred or reasonable, or whether a cost is already included in the "
    "guideline figure. For those questions you can ask a lawyer, your court's "
    "self-help center, or its family law facilitator."
)
NOTE_ADDITIONAL_BASIC = (
    "The basic support amount above is this report's own arithmetic. It does "
    "not apply the rebuttal factors of FC 4057 (see FC 4061(b)(1)), and FC "
    "4061(d) reduces by the basic support \"ordered to be paid\", which can "
    "differ from this figure."
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


def _percent_text(hundredths):
    return cents_text(hundredths)


def _additional_end_lines(end, a_typed, b_typed):
    """The reduction lines for one end of the support amount."""
    lines = [ADDITIONAL_REDUCTION_HEADING]
    if end.support_cents == 0:
        lines.append(ADDITIONAL_ZERO_SUPPORT_LINE)
        return lines
    support = cents_text(end.support_cents)
    if end.paying == "A":
        paying, typed, reduced = "A", a_typed, end.a_reduced
        other, other_figure = "B", end.b_reduced
    else:
        paying, typed, reduced = "B", b_typed, end.b_reduced
        other, other_figure = "A", end.a_reduced
    lines.append(
        ADDITIONAL_PAYER_LINE % (paying, money(typed), support, money(reduced))
    )
    lines.append(ADDITIONAL_NOT_INCREASED_LINE % (other, money(other_figure)))
    return lines


def _additional_lines(result):
    """The additional child support section, for any GuidelineResult."""
    extra = result.additional
    if extra is None:
        return [ADDITIONAL_REST_HEADING, ADDITIONAL_REST_LINE]

    def cost(label, value):
        return label % (ADDITIONAL_NOT_ENTERED if value is None else money(value))

    lines = [
        ADDITIONAL_HEADING,
        ADDITIONAL_COSTS_LINE,
        cost(ADDITIONAL_CHILDCARE_LABEL, extra.childcare),
        cost(ADDITIONAL_HEALTH_LABEL, extra.health),
        ADDITIONAL_TOTAL_LINE % cents_text(extra.total_cents),
    ]
    if extra.share_percent is not None:
        lines += [
            ADDITIONAL_CHOSEN_LINE
            % (plain(extra.share_percent, 2), plain(100 - extra.share_percent, 2)),
            ADDITIONAL_CHOSEN_AMOUNT_LINE % ("A", cents_text(extra.a_cents)),
            ADDITIONAL_CHOSEN_AMOUNT_LINE % ("B", cents_text(extra.b_cents)),
        ]
        return lines
    lines += [
        ADDITIONAL_FIGURES_LINE,
        ADDITIONAL_A_TYPED_LINE % money(extra.a_adjusted),
        ADDITIONAL_B_TYPED_LINE % money(extra.b_adjusted),
    ]
    for end in extra.ends:
        if extra.ranged:
            heading = ADDITIONAL_TOP_LINE if end.label == "top" else ADDITIONAL_BOTTOM_LINE
            lines.append(heading % cents_text(end.support_cents))
        lines += _additional_end_lines(end, extra.a_adjusted, extra.b_adjusted)
        denominator = money(end.a_reduced + end.b_reduced)
        lines += [
            ADDITIONAL_SPLIT_HEADING,
            ADDITIONAL_SPLIT_LINE
            % (
                "A",
                money(end.a_reduced),
                denominator,
                _percent_text(end.a_percent_hundredths),
                cents_text(end.a_cents),
            ),
            ADDITIONAL_SPLIT_LINE
            % (
                "B",
                money(end.b_reduced),
                denominator,
                _percent_text(end.b_percent_hundredths),
                cents_text(end.b_cents),
            ),
        ]
    return lines


def _additional_notes(result):
    extra = result.additional
    if extra is None:
        return []
    notes = []
    if extra.share_percent is None:
        notes.append(NOTE_ADDITIONAL_INCOME)
    notes += [NOTE_ADDITIONAL_MAY, NOTE_ADDITIONAL_DECIDE, NOTE_ADDITIONAL_BASIC]
    return notes


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
    body += [""] + _additional_lines(result)
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
    body += _additional_notes(result)
    body += ["", CLOSING_LINE]
    return "\f".join(paginate(body))
