"""Plain-text report for the step 1 guideline result.

Every page starts with the identity line. There is one way to produce report
text, render_report(result), and it takes no option that could change that.
"""

from family_law_toolkit import TOOLKIT_NAME, __version__
from family_law_toolkit.support.guideline import fixed, money, plain

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

LOW_INCOME_HEADING = "Low-income adjustment (FC 4055(b)(7); range under FC 4055(c))"
READING_R2_LINE = (
    "  This toolkit reads the monthly threshold as the hourly minimum wage "
    "x 40 x 52 / 12 (FC 4055(b)(7))."
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
            "a rebuttable presumption applies (FC 4055(b)(7)).",
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


def render_report(result):
    """Return the full report text for a GuidelineResult."""
    hn = result.a_ndi if result.high_earner == "A" else result.b_ndi
    body = [
        "Guideline child support, step 1 (California Family Code section 4055)",
        "Amounts are monthly dollars, rounded to the nearest cent (halves round up).",
        "",
        "Inputs as given",
        "  Parent A net disposable income: %s" % money(result.a_ndi),
        "  Parent B net disposable income: %s" % money(result.b_ndi),
        "  Parent A's share of time: %s%%" % plain(result.a_time_percent, 2),
        "  Number of children: %d" % result.children,
        "  Hourly minimum wage used: %s" % money(result.minimum_wage_hourly),
        "",
        "Formula",
        "  Total net disposable income, TN (FC 4055(b)(1)(E)): %s" % money(result.tn),
        "  High earner (FC 4055(b)(1)(C)): %s" % _parent(result.high_earner),
        "  High earner's share of time, H%% (FC 4055(b)(1)(D)): %s%%"
        % plain(result.h_percent, 2),
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
    body += ["", NOTE_NDI, NOTE_TIME_SHARE]
    return "\f".join(paginate(body))
