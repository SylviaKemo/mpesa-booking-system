"""
Seed the catalogue.

The values mirror frontend/src/data/services.ts, which was the source of truth
until now. Once this runs, the database is: the server prices every booking from
these rows and never trusts an amount sent by a client.

Idempotent — safe to run on every deploy.
"""

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Addition, LashSet, Tier

SETS: list[dict] = [
    {
        "id": "wispy",
        "name": "Wispy set",
        "blurb": "Textured, feathered spikes for a soft fluttery finish.",
        "image_url": "https://swiftill.co.ke/uploads/businesses/katiani-styles/services/basic-wispy/1de49dea14664f6588b3c30dda5455a4.jpeg",
        "image_alt": "Wispy lash set",
        "tiers": [
            {"id": "wispy-basic", "label": "Basic", "minutes": 20, "amount_kes": 600},
            {"id": "wispy-mid", "label": "Mid volume", "minutes": 25, "amount_kes": 700},
            {"id": "wispy-vol", "label": "Volume", "minutes": 30, "amount_kes": 800},
        ],
    },
    {
        "id": "cat",
        "name": "Cat eye",
        "blurb": "Length pushed to the outer corner for a lifted, elongated eye.",
        "image_url": "https://swiftill.co.ke/uploads/businesses/katiani-styles/services/basiccat-eye/49424dc25df240d99faf214406ef98a1.jpeg",
        "image_alt": "Cat eye lash set",
        "tiers": [
            {"id": "cat-basic", "label": "Basic", "minutes": 20, "amount_kes": 600},
            {"id": "cat-mid", "label": "Mid volume", "minutes": 25, "amount_kes": 700},
            {"id": "cat-vol", "label": "Volume", "minutes": 30, "amount_kes": 900},
        ],
    },
    {
        "id": "classic",
        "name": "Classic set",
        "blurb": "One extension per natural lash — a simple, natural set. Best place to start.",
        "image_url": "https://swiftill.co.ke/uploads/businesses/katiani-styles/services/mid-vol-classic/f3875edac0014d6fa2ecc06eb8426ef2.jpeg",
        "image_alt": "Classic lash set",
        "tiers": [
            {
                "id": "classic",
                "label": "Classic",
                "minutes": 20,
                "amount_kes": 600,
                "note": "for beginners",
            },
        ],
    },
]

ADDITIONS: list[dict] = [
    {"id": "removal", "label": "Removal", "amount_kes": 300, "minutes": 15},
    {"id": "charms", "label": "Lash charms", "amount_kes": 100, "minutes": 5},
    {"id": "colour", "label": "Colour add-ons", "amount_kes": 100, "minutes": 5},
    {"id": "glitter", "label": "Glitter spikes", "amount_kes": 100, "minutes": 5},
]


def seed_catalogue(db: Session) -> None:
    """
    Insert or update the catalogue in place.

    Rows are merged rather than deleted and recreated, so bookings that
    reference a tier keep pointing at a row that still exists.
    """
    for set_position, set_data in enumerate(SETS):
        tiers = set_data["tiers"]

        db.merge(
            LashSet(
                id=set_data["id"],
                name=set_data["name"],
                blurb=set_data["blurb"],
                image_url=set_data["image_url"],
                image_alt=set_data["image_alt"],
                position=set_position,
            )
        )
        # Flushed before the tiers so the foreign key target exists.
        db.flush()

        for tier_position, tier in enumerate(tiers):
            db.merge(
                Tier(
                    id=tier["id"],
                    set_id=set_data["id"],
                    label=tier["label"],
                    amount_kes=tier["amount_kes"],
                    minutes=tier["minutes"],
                    note=tier.get("note"),
                    position=tier_position,
                )
            )

    for position, addition in enumerate(ADDITIONS):
        db.merge(
            Addition(
                id=addition["id"],
                label=addition["label"],
                amount_kes=addition["amount_kes"],
                minutes=addition["minutes"],
                position=position,
            )
        )

    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        seed_catalogue(db)
        print("Catalogue seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
