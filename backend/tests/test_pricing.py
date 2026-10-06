import math

import pytest
from sqlalchemy.orm import Session

from app.services.pricing import PricingError, deposit_for, quote


@pytest.mark.usefixtures("seeded")
def test_quote_prices_from_the_catalogue(db: Session) -> None:
    result = quote(db, "wispy-mid", ["removal", "charms"])

    assert result.amount_kes == 700 + 300 + 100
    assert result.minutes == 25 + 15 + 5
    assert result.deposit_kes == 550


@pytest.mark.usefixtures("seeded")
def test_quote_ignores_a_repeated_addition(db: Session) -> None:
    """Sending the same extra twice must not charge for it twice."""
    once = quote(db, "wispy-mid", ["removal"])
    twice = quote(db, "wispy-mid", ["removal", "removal"])

    assert twice.amount_kes == once.amount_kes
    assert len(twice.additions) == 1


@pytest.mark.usefixtures("seeded")
def test_quote_rejects_an_unknown_tier(db: Session) -> None:
    with pytest.raises(PricingError, match="tier"):
        quote(db, "no-such-tier", [])


@pytest.mark.usefixtures("seeded")
def test_quote_rejects_an_unknown_addition(db: Session) -> None:
    with pytest.raises(PricingError, match="additions"):
        quote(db, "wispy-mid", ["gold-leaf"])


@pytest.mark.usefixtures("seeded")
def test_quote_rejects_a_withdrawn_item(db: Session) -> None:
    """A deactivated item is off the menu, so it cannot be booked either."""
    from app.models import Addition, Tier

    db.get(Addition, "glitter").is_active = False
    db.get(Tier, "cat-vol").is_active = False
    db.commit()

    with pytest.raises(PricingError):
        quote(db, "wispy-mid", ["glitter"])
    with pytest.raises(PricingError):
        quote(db, "cat-vol", [])


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (600, 300),
        (700, 350),
        (1100, 550),
        (900, 450),
        (100, 100),
        (0, 100),
    ],
)
def test_deposit_is_half_to_the_nearest_fifty_with_a_floor(
    amount: int, expected: int
) -> None:
    assert deposit_for(amount) == expected


def test_deposit_matches_the_frontend_rounding_rule() -> None:
    """
    Python's round() is half-to-even and JavaScript's Math.round is half-up, so
    a total of 1,250 would otherwise be quoted 600 by one and 650 by the other.
    """
    for amount in range(0, 5001, 50):
        as_javascript_would = max(100, math.floor(amount * 0.5 / 50 + 0.5) * 50)
        assert deposit_for(amount) == as_javascript_would, amount
