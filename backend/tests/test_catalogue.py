import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Addition, LashSet, Tier
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
        for model in (Tier, LashSet, Addition):
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
        for model in (Tier, LashSet, Addition):
            db.query(model).delete()
        db.commit()
