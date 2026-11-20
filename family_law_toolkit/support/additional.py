# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Additional child support (Family Code 4062), split between the parents under
Family Code 4061: the arithmetic only, no printing.

Every figure is an exact fractions.Fraction. Only a displayed amount is rounded,
to the cent, half up, and the reduction of FC 4061(d) uses the support amount
as the report prints it (to the cent), so a person can repeat it by hand.
"""

import dataclasses
from fractions import Fraction

from family_law_toolkit.support.guideline import _cents, money

HELP_REFERRAL = (
    "For help with these figures you can ask a lawyer, your court's "
    "self-help center, or its family law facilitator."
)


class AdditionalSupportRefused(Exception):
    """The split cannot be worked out; the message is a complete sentence."""


@dataclasses.dataclass(frozen=True)
class SplitEnd:
    """The FC 4061(d) reduction and the proportional split at one support amount."""

    label: str  # "top" or "bottom"; only shown when the amount is a range
    support_cents: int
    paying: str  # "A", "B" or "none"
    a_reduced: Fraction
    b_reduced: Fraction
    a_cents: int
    b_cents: int
    a_percent_hundredths: int  # Parent A's share, in hundredths of a percent
    b_percent_hundredths: int  # 10000 minus A's, so the two always make 100.00


@dataclasses.dataclass(frozen=True)
class AdditionalSupport:
    childcare: object  # Fraction, or None when not entered
    health: object  # Fraction, or None when not entered
    total_cents: int
    a_adjusted: object  # Fraction as typed, or None when a share was typed
    b_adjusted: object
    share_percent: object  # Fraction, or None when the split is proportional
    a_cents: int  # only for a typed share; otherwise see ends
    b_cents: int
    ranged: bool
    ends: tuple  # SplitEnd per end of the support amount; empty for a typed share


def _split_cents(total_cents, a_exact):
    """Parent A's exact dollars rounded half up to cents; Parent B's cents are
    the rest of the total (spec 4.3, A2)."""
    a_cents = _cents(a_exact)
    return a_cents, total_cents - a_cents


def _end(result, label, support_cents, a_adjusted, b_adjusted, total_cents, ranged):
    support = Fraction(support_cents, 100)
    a_reduced, b_reduced = a_adjusted, b_adjusted
    if result.payer == "A":
        a_reduced = a_adjusted - support
    elif result.payer == "B":
        b_reduced = b_adjusted - support
    if a_reduced < 0 or b_reduced < 0 or a_reduced + b_reduced <= 0:
        message = (
            "After FC 4061(d) takes basic support from the paying parent's figure, "
            "the figures are Parent A: %s and Parent B: %s, and a share cannot be "
            "worked out from them. " % (money(a_reduced), money(b_reduced))
            + HELP_REFERRAL
        )
        if ranged:
            message = "At the %s of the support range (support %s): %s" % (
                label,
                money(support),
                message,
            )
        raise AdditionalSupportRefused(message)
    total_figure = a_reduced + b_reduced
    a_cents, b_cents = _split_cents(
        total_cents, Fraction(total_cents, 100) * a_reduced / total_figure
    )
    a_hundredths = _cents(a_reduced / total_figure * 100)
    return SplitEnd(
        label=label,
        support_cents=support_cents,
        paying=result.payer,
        a_reduced=a_reduced,
        b_reduced=b_reduced,
        a_cents=a_cents,
        b_cents=b_cents,
        a_percent_hundredths=a_hundredths,
        b_percent_hundredths=10000 - a_hundredths,
    )


def compute_additional(
    result, childcare, health, a_adjusted, b_adjusted, a_share_percent
):
    """Split the typed costs. Arguments after result are Fractions, or None when
    not given. Raises AdditionalSupportRefused when no share can be worked out."""
    total = (childcare or Fraction(0)) + (health or Fraction(0))
    total_cents = int(total * 100)
    if a_share_percent is not None:
        a_cents, b_cents = _split_cents(total_cents, total * a_share_percent / 100)
        return AdditionalSupport(
            childcare=childcare,
            health=health,
            total_cents=total_cents,
            a_adjusted=None,
            b_adjusted=None,
            share_percent=a_share_percent,
            a_cents=a_cents,
            b_cents=b_cents,
            ranged=False,
            ends=(),
        )
    ranged = result.lia.applies
    ends = [("top", _cents(result.support))]
    if ranged:
        ends.append(("bottom", _cents(result.lia.range_low)))
    built = tuple(
        _end(result, label, cents, a_adjusted, b_adjusted, total_cents, ranged)
        for label, cents in ends
    )
    return AdditionalSupport(
        childcare=childcare,
        health=health,
        total_cents=total_cents,
        a_adjusted=a_adjusted,
        b_adjusted=b_adjusted,
        share_percent=None,
        a_cents=0,
        b_cents=0,
        ranged=ranged,
        ends=built,
    )
