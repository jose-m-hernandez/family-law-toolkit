"""The California guideline child-support formula (Family Code 4055), with the
FC 4055(b)(8) allocation per child.

Net disposable income is an input here; Family Code 4059 deductions are not
computed. All arithmetic is exact (fractions.Fraction); only the display
helpers round, to cents, half-up, from the exact value.
"""

import dataclasses
from decimal import Decimal, InvalidOperation
from fractions import Fraction

# Table rows of FC 4055(b)(3). Each row is
#   (upper bound of TN, constant, coefficient of TN, coefficient of 1/TN)
# so the row fraction is  constant + coefficient_tn * TN + coefficient_inv / TN.
# Upper bounds are inclusive (reading R3); None means "over $15,000".
K_ROWS = (
    # row 1, FC 4055(b)(3): $0-2,900: 0.165 + TN/82,857
    (Fraction(2900), Fraction("0.165"), Fraction(1, 82857), Fraction(0)),
    # row 2, FC 4055(b)(3): $2,901-5,000: 0.131 + TN/42,149
    (Fraction(5000), Fraction("0.131"), Fraction(1, 42149), Fraction(0)),
    # row 3, FC 4055(b)(3): $5,001-10,000: 0.250
    (Fraction(10000), Fraction("0.250"), Fraction(0), Fraction(0)),
    # row 4, FC 4055(b)(3): $10,001-15,000: 0.10 + 1,499/TN
    (Fraction(15000), Fraction("0.10"), Fraction(0), Fraction(1499)),
    # row 5, FC 4055(b)(3): over $15,000: 0.12 + 1,200/TN
    (None, Fraction("0.12"), Fraction(0), Fraction(1200)),
)

# Multipliers for more than one child, FC 4055(b)(4).
MULTIPLIERS = {
    1: Fraction(1),  # one child: no multiplier, FC 4055(b)(4)
    2: Fraction("1.6"),  # FC 4055(b)(4)
    3: Fraction(2),  # FC 4055(b)(4)
    4: Fraction("2.3"),  # FC 4055(b)(4)
    5: Fraction("2.5"),  # FC 4055(b)(4)
    6: Fraction("2.625"),  # FC 4055(b)(4)
    7: Fraction("2.75"),  # FC 4055(b)(4)
    8: Fraction("2.813"),  # FC 4055(b)(4)
    9: Fraction("2.844"),  # FC 4055(b)(4)
    10: Fraction("2.86"),  # FC 4055(b)(4)
}

# FC 4055(b)(7): full-time minimum wage, 40 hours a week, 52 weeks a year,
# turned into a monthly figure by dividing by 12 (readings R1, R2).
HOURS_PER_WEEK = 40
WEEKS_PER_YEAR = 52
MONTHS_PER_YEAR = 12

SAME_TIME_SHARING_CHOICES = ("yes", "no")  # the optional input, plan reading R10

MAX_DECIMALS = 2
MAX_ABS_EXPONENT = 15  # amounts must stay below 10**16 so parsing stays cheap


@dataclasses.dataclass(frozen=True)
class LowIncomeAdjustment:
    """The FC 4055(b)(7) test and the FC 4055(c) range."""

    threshold: Fraction
    applies: bool
    max_reduction: Fraction
    range_low: Fraction
    range_high: Fraction


@dataclasses.dataclass(frozen=True)
class GuidelineResult:
    """Exact results of the step 1 computation, named as in the golden data."""

    tn: Fraction
    high_earner: str
    h_percent: Fraction
    k_row: int
    k: Fraction
    cs_formula: Fraction
    multiplier: Fraction
    cs_total: Fraction
    payer: str
    support: Fraction
    lia: LowIncomeAdjustment
    # The inputs as given, so the report can echo them.
    a_ndi: Fraction
    b_ndi: Fraction
    a_time_percent: Fraction
    children: int
    minimum_wage_hourly: Fraction
    # Optional input (R10): do all the children share one time-sharing
    # arrangement? None when it was not given.
    same_time_sharing_arrangement: object = None


@dataclasses.dataclass(frozen=True)
class AllocationEnd:
    """The FC 4055(b)(8) allocation for one end of the amount.

    exact_cumulative: the exact amounts for 1, 2, ... n children (Fractions).
    cumulative: the same amounts rounded half-up to whole cents (ints).
    per_child: youngest first; the first child's cumulative amount, then the
    differences between consecutive rounded cumulative amounts (reading R8).
    """

    exact_cumulative: tuple
    cumulative: tuple
    per_child: tuple


@dataclasses.dataclass(frozen=True)
class Allocation:
    """top: no low-income reduction. bottom: the largest reduction (R7), or None."""

    top: AllocationEnd
    bottom: object = None


def _parse_decimal(name, value, max_decimals=MAX_DECIMALS):
    """Parse a decimal string into a finite Decimal with few decimals."""
    if not isinstance(value, str):
        raise ValueError("%s must be a decimal string" % name)
    try:
        number = Decimal(value.strip())
    except InvalidOperation:
        raise ValueError("%s is not a decimal number" % name) from None
    if not number.is_finite():
        raise ValueError("%s must be a finite number" % name)
    if number.as_tuple().exponent < -max_decimals:
        raise ValueError("%s has more than %d decimals" % (name, max_decimals))
    if number.adjusted() > MAX_ABS_EXPONENT:
        raise ValueError("%s is too large" % name)
    return number


def _parse_amount(name, value):
    number = _parse_decimal(name, value)
    if number < 0:
        raise ValueError("%s must not be negative" % name)
    return Fraction(number)


def _parse_percent(name, value):
    number = _parse_decimal(name, value)
    if number < 0 or number > 100:
        raise ValueError("%s must be between 0 and 100" % name)
    return Fraction(number)


def _parse_wage(name, value):
    number = _parse_decimal(name, value)
    if number <= 0:
        raise ValueError("%s must be greater than zero" % name)
    return Fraction(number)


def _parse_children(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s must be a whole number" % name)
    if value not in MULTIPLIERS:
        raise ValueError("%s must be between 1 and 10" % name)
    return value


def _parse_same_time_sharing(name, value):
    if value is None:
        return None
    if not isinstance(value, str) or value not in SAME_TIME_SHARING_CHOICES:
        raise ValueError("%s must be yes or no" % name)
    return value


def k_row_for(tn):
    """Return the 1-based K table row for TN (FC 4055(b)(3), reading R3)."""
    for index, (upper, _, _, _) in enumerate(K_ROWS, start=1):
        if upper is None or tn <= upper:
            return index
    raise AssertionError("unreachable: the last row has no upper bound")


def row_fraction(row, tn):
    """The fraction of FC 4055(b)(3) for a table row at total income TN."""
    _, constant, coefficient_tn, coefficient_inv = K_ROWS[row - 1]
    value = constant + coefficient_tn * tn
    if coefficient_inv:
        value += coefficient_inv / tn
    return value


def low_income_threshold(minimum_wage_hourly):
    """Monthly full-time minimum-wage income (FC 4055(b)(7); readings R1, R2)."""
    return (
        Fraction(minimum_wage_hourly)
        * HOURS_PER_WEEK
        * WEEKS_PER_YEAR
        / MONTHS_PER_YEAR
    )


def compute(
    a_ndi,
    b_ndi,
    a_time_percent,
    children,
    minimum_wage_hourly,
    same_time_sharing_arrangement=None,
):
    """Run the guideline formula; inputs are decimal strings, an int and, optionally, yes or no."""
    a_net = _parse_amount("a_ndi", a_ndi)
    b_net = _parse_amount("b_ndi", b_ndi)
    a_time = _parse_percent("a_time_percent", a_time_percent)
    count = _parse_children("children", children)
    wage = _parse_wage("minimum_wage_hourly", minimum_wage_hourly)
    arrangement = _parse_same_time_sharing(
        "same_time_sharing_arrangement", same_time_sharing_arrangement
    )

    # FC 4055(b)(1)(E): TN is the total of both parents' NDI.
    tn = a_net + b_net
    # FC 4055(b)(1)(C): HN is the high earner's NDI; a tie goes to Parent A.
    high_earner = "A" if a_net >= b_net else "B"
    low_earner = "B" if high_earner == "A" else "A"
    hn = a_net if high_earner == "A" else b_net
    # FC 4055(b)(1)(D): H% is the high earner's share of time (kept as a
    # percent; one time-share applies to all children).
    h_percent = a_time if high_earner == "A" else 100 - a_time
    h_fraction = h_percent / 100

    # FC 4055(b)(3): K = (1 + H%) up to 50 percent, (2 - H%) above, times the row fraction.
    k_row = k_row_for(tn)
    time_factor = 1 + h_fraction if h_percent <= 50 else 2 - h_fraction
    k = time_factor * row_fraction(k_row, tn)

    # FC 4055(a): CS = K[HN - (H%)(TN)].
    cs_formula = k * (hn - h_fraction * tn)
    # FC 4055(b)(4): multiply by the children multiplier.
    multiplier = MULTIPLIERS[count]
    cs_total = cs_formula * multiplier

    # FC 4055(b)(5): a positive result is paid by the high earner, a negative
    # one by the lower earner.
    if cs_total > 0:
        payer = high_earner
    elif cs_total < 0:
        payer = low_earner
    else:
        payer = "none"
    support = abs(cs_total)

    # FC 4055(b)(7), (c): the low-income test on the payer's NDI, strictly
    # "less than", reported as a range and never as a single figure.
    threshold = low_income_threshold(wage)
    payer_ndi = {"A": a_net, "B": b_net}.get(payer)
    applies = payer_ndi is not None and payer_ndi < threshold
    if applies:
        max_reduction = support * (threshold - payer_ndi) / threshold
    else:
        max_reduction = Fraction(0)
    lia = LowIncomeAdjustment(
        threshold=threshold,
        applies=applies,
        max_reduction=max_reduction,
        range_low=support - max_reduction,
        range_high=support,
    )
    return GuidelineResult(
        tn=tn,
        high_earner=high_earner,
        h_percent=h_percent,
        k_row=k_row,
        k=k,
        cs_formula=cs_formula,
        multiplier=multiplier,
        cs_total=cs_total,
        payer=payer,
        support=support,
        lia=lia,
        a_ndi=a_net,
        b_ndi=b_net,
        a_time_percent=a_time,
        children=count,
        minimum_wage_hourly=wage,
        same_time_sharing_arrangement=arrangement,
    )


def _cents(value):
    """Round a non-negative exact Fraction to whole cents, half-up (reading R4)."""
    return (200 * value.numerator + value.denominator) // (2 * value.denominator)


def allocation(result):
    """The FC 4055(b)(8) allocation per child, or None when none is shown.

    It is shown only for two or more children, when the person said the
    children share one time-sharing arrangement (yes), and when there is a
    paying parent. The exact amount for k children is |CS| x the (b)(4)
    multiplier for k (the (b)(1)-(b)(4) amounts); each is rounded to the cent
    for display, and a child's amount is the difference between the displayed
    amounts for consecutive child counts (reading R8). When the (b)(7)
    adjustment applies, the bottom end uses each amount reduced by the largest
    permitted reduction, the same fraction for every child count (reading R7).
    """
    if (
        result.children < 2
        or result.same_time_sharing_arrangement != "yes"
        or result.payer == "none"
    ):
        return None
    base = abs(result.cs_formula)
    factors = [("top", Fraction(1))]
    if result.lia.applies:
        factors.append(("bottom", 1 - result.lia.max_reduction / result.support))
    ends = {}
    for name, factor in factors:
        exact = tuple(
            base * MULTIPLIERS[count] * factor for count in range(1, result.children + 1)
        )
        shown = tuple(_cents(value) for value in exact)
        per_child = (shown[0],) + tuple(b - a for a, b in zip(shown, shown[1:]))
        ends[name] = AllocationEnd(
            exact_cumulative=exact, cumulative=shown, per_child=per_child
        )
    return Allocation(top=ends["top"], bottom=ends.get("bottom"))


def cents_text(cents):
    """Format whole cents as dollars and cents."""
    return "%d.%02d" % divmod(cents, 100)


def fixed(value, places):
    """Format an exact Fraction with fixed decimals, rounded half-up (reading R4).

    Halves round away from zero, so a negative value mirrors its positive twin.
    """
    scale = 10 ** places
    numerator = abs(value.numerator) * scale
    denominator = value.denominator
    rounded = (2 * numerator + denominator) // (2 * denominator)
    sign = "-" if value < 0 and rounded else ""
    whole, part = divmod(rounded, scale)
    return "%s%d.%0*d" % (sign, whole, places, part)


def money(value):
    """Format an exact Fraction as dollars and cents, rounded half-up."""
    return fixed(value, 2)


def plain(value, places):
    """Like fixed, with trailing zeros (and a bare point) removed."""
    text = fixed(value, places)
    return text.rstrip("0").rstrip(".") if "." in text else text
