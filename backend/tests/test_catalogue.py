import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Addition, Booking, BookingAddition, LashSet, Tier
from app.seed import ADDITIONS, SETS, seed_catalogue


@pytest.mark.usefixtures("seeded")
def test_catalogue_returns_every_set_and_addition(client: TestClient) -> None:
    body = client.get("/api/catalogue").json()

    assert [s["id"] for s in body["sets"]] == [s["id"] for s in SETS]
    assert [a["id"] for a in body["additions"]] == [a["id"] for a in ADDITIONS]


@pytest.mark.usefixtures("seeded")
def test_sets_and_tiers_come_back_in_display_order(client: TestClient) -> None:
    """
    Order is editorial, not alphabetical. Without the stored position the
    database could return any order and the menu would render wrong.
    """
    body = client.get("/api/catalogue").json()

    assert [s["id"] for s in body["sets"]] == ["wispy", "cat", "classic"]

    wispy = next(s for s in body["sets"] if s["id"] == "wispy")
    assert [t["id"] for t in wispy["tiers"]] == [
        "wispy-basic",
        "wispy-mid",
        "wispy-vol",
    ]


@pytest.mark.usefixtures("seeded")
def test_prices_match_the_seeded_price_list(client: TestClient) -> None:
    """These amounts are what the server will charge; a silent drift is a bug."""
    body = client.get("/api/catalogue").json()
    tiers = {t["id"]: t for s in body["sets"] for t in s["tiers"]}

    assert tiers["wispy-basic"]["amount_kes"] == 600
    assert tiers["wispy-mid"]["amount_kes"] == 700
    assert tiers["cat-vol"]["amount_kes"] == 900
    assert tiers["wispy-mid"]["minutes"] == 25

    additions = {a["id"]: a for a in body["additions"]}
    assert additions["removal"]["amount_kes"] == 300
    assert additions["removal"]["minutes"] == 15
    assert additions["charms"]["amount_kes"] == 100


@pytest.mark.usefixtures("seeded")
def test_tier_note_is_carried_through_and_optional(client: TestClient) -> None:
    body = client.get("/api/catalogue").json()
    tiers = {t["id"]: t for s in body["sets"] for t in s["tiers"]}

    assert tiers["classic"]["note"] == "for beginners"
    assert tiers["wispy-basic"]["note"] is None


@pytest.mark.usefixtures("seeded")
def test_additions_card_copy_is_included(client: TestClient) -> None:
    card = client.get("/api/catalogue").json()["additions_card"]

    assert card["name"] == "Additions"
    assert card["image_url"].startswith("https://")


def test_catalogue_is_empty_before_seeding(client: TestClient) -> None:
    """An unseeded deploy returns an empty menu rather than failing."""
    body = client.get("/api/catalogue").json()

    assert body["sets"] == []
    assert body["additions"] == []


def test_seeding_twice_does_not_duplicate_rows(db: Session) -> None:
    """Seeding runs on every deploy, so it has to be idempotent."""
    try:
        seed_catalogue(db)
        seed_catalogue(db)

        assert db.query(LashSet).count() == len(SETS)
        assert db.query(Tier).count() == sum(len(s["tiers"]) for s in SETS)
        assert db.query(Addition).count() == len(ADDITIONS)
    finally:
        for model in (BookingAddition, Booking, Tier, LashSet, Addition):
            db.query(model).delete()
        db.commit()


def test_reseeding_updates_a_changed_price(db: Session) -> None:
    """
    A price change must reach existing rows, not be skipped as already present.
    Rows are merged rather than deleted so bookings keep referencing a live tier.
    """
    try:
        seed_catalogue(db)
        tier = db.get(Tier, "wispy-mid")
        assert tier is not None
        tier.amount_kes = 1
        db.commit()

        seed_catalogue(db)

        db.refresh(tier)
        assert tier.amount_kes == 700
    finally:
        for model in (BookingAddition, Booking, Tier, LashSet, Addition):
            db.query(model).delete()
        db.commit()


@pytest.mark.usefixtures("seeded")
def test_withdrawn_addition_leaves_the_menu(client: TestClient, db: Session) -> None:
    """
    Removing an item from the seed data must take it off the menu.

    Deactivation, not deletion: the row survives so a booking that referenced
    it still resolves.
    """
    addition = db.get(Addition, "glitter")
    assert addition is not None
    addition.is_active = False
    db.commit()

    body = client.get("/api/catalogue").json()

    assert "glitter" not in [a["id"] for a in body["additions"]]
    assert db.get(Addition, "glitter") is not None


@pytest.mark.usefixtures("seeded")
def test_withdrawn_tier_leaves_its_set_but_the_set_remains(
    client: TestClient, db: Session
) -> None:
    tier = db.get(Tier, "wispy-vol")
    assert tier is not None
    tier.is_active = False
    db.commit()

    body = client.get("/api/catalogue").json()
    wispy = next(s for s in body["sets"] if s["id"] == "wispy")

    assert [t["id"] for t in wispy["tiers"]] == ["wispy-basic", "wispy-mid"]


@pytest.mark.usefixtures("seeded")
def test_withdrawn_set_leaves_the_menu(client: TestClient, db: Session) -> None:
    lash_set = db.get(LashSet, "cat")
    assert lash_set is not None
    lash_set.is_active = False
    db.commit()

    body = client.get("/api/catalogue").json()

    assert [s["id"] for s in body["sets"]] == ["wispy", "classic"]


def test_reseeding_deactivates_items_dropped_from_the_data(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Without this reconciliation the catalogue could only grow, and a withdrawn
    service would stay bookable forever.
    """
    import app.seed as seed_module

    try:
        seed_catalogue(db)

        monkeypatch.setattr(
            seed_module,
            "ADDITIONS",
            [a for a in ADDITIONS if a["id"] != "glitter"],
        )
        seed_catalogue(db)

        glitter = db.get(Addition, "glitter")
        assert glitter is not None, "row must survive so bookings still resolve"
        db.refresh(glitter)
        assert glitter.is_active is False
        assert db.get(Addition, "removal").is_active is True
    finally:
        for model in (BookingAddition, Booking, Tier, LashSet, Addition):
            db.query(model).delete()
        db.commit()


def test_additions_card_cannot_be_mutated_through_a_response() -> None:
    """One instance is shared by every response, so it must be immutable."""
    from pydantic import ValidationError

    from app.api.catalogue import ADDITIONS_CARD

    with pytest.raises(ValidationError):
        ADDITIONS_CARD.name = "MUTATED"
