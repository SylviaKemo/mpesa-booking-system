"""
Pricing. The server's answer, never the client's.

A request names tier and addition *ids*; everything monetary is read from the
catalogue rows those ids resolve to. No amount in a request body is read.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Addition, Tier


class PricingError(Exception):
    """A requested item does not exist or is no longer offered."""


@dataclass(frozen=True)
class Quote:
    tier: Tier
    additions: list[Addition]
    amount_kes: int
    minutes: int
    deposit_kes: int


def quote(db: Session, tier_id: str, addition_ids: list[str]) -> Quote:
    """
    Price a selection from the catalogue.

    Raises PricingError if the tier or any addition is unknown or withdrawn, so
    a client cannot book something that is no longer on the menu.
    """
    tier = db.scalar(select(Tier).where(Tier.id == tier_id, Tier.is_active))
    if tier is None:
        raise PricingError(f"Unknown or unavailable tier: {tier_id!r}")

    # Deduplicated: sending the same addition twice must not charge twice.
    wanted = list(dict.fromkeys(addition_ids))

    additions: list[Addition] = []
    if wanted:
        found = db.scalars(
            select(Addition)
            .where(Addition.id.in_(wanted), Addition.is_active)
            .order_by(Addition.position)
        ).all()
        by_id = {a.id: a for a in found}

        missing = [a for a in wanted if a not in by_id]
        if missing:
            raise PricingError(
                f"Unknown or unavailable additions: {', '.join(sorted(missing))}"
            )
        additions = list(found)

    amount = tier.amount_kes + sum(a.amount_kes for a in additions)
    minutes = tier.minutes + sum(a.minutes for a in additions)

    return Quote(
        tier=tier,
        additions=additions,
        amount_kes=amount,
        minutes=minutes,
        deposit_kes=deposit_for(amount),
    )


def deposit_for(amount_kes: int) -> int:
    """
    Half the total, to the nearest 50 KES, never below 100.

    Rounds to nearest rather than up, matching the prototype the frontend was
    built from — confirmed as the intended behaviour.

    Integer arithmetic on purpose, for two reasons. Python's round() is
    half-to-even while the frontend's Math.round is half-up, so on a total of
    1,250 they would quote 600 and 650 — the client would see one deposit and be
    charged another. And floats have no business near money. The expression is
    floor(amount / 100 + 1/2) half-steps of 50, done without leaving ints.
    """
    half_steps = (2 * amount_kes + 100) // 200
    return max(100, half_steps * 50)
