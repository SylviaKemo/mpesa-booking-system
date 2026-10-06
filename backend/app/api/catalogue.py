from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Addition, LashSet
from app.schemas.catalogue import AdditionsCardOut, CatalogueOut

router = APIRouter(tags=["catalogue"])

# Copy for the additions card. It is presentation, not priced catalogue data —
# a single-row table would buy nothing — so it lives here rather than in the
# database, and still reaches the client in the same response.
ADDITIONS_CARD = AdditionsCardOut(
    name="Additions",
    blurb="Pick as many as you like — these stack on top of your set.",
    image_url="https://swiftill.co.ke/uploads/businesses/katiani-styles/services/lash-removal/f1262cc673a8498c84a592c39a64cb7b.jpeg",
    image_alt="Lash additions and removal",
)


@router.get("/catalogue", response_model=CatalogueOut)
def get_catalogue(db: Session = Depends(get_db)) -> CatalogueOut:
    """
    The menu, in display order.

    This is the server's price list. From the booking slice onward a client
    sends tier and addition *ids*; amounts are read from these rows and an
    amount supplied by a client is never trusted.
    """
    sets = db.scalars(
        # selectinload avoids one query per set for its tiers.
        select(LashSet).options(selectinload(LashSet.tiers)).order_by(LashSet.position)
    ).all()

    additions = db.scalars(select(Addition).order_by(Addition.position)).all()

    return CatalogueOut.model_validate(
        {"sets": sets, "additions": additions, "additions_card": ADDITIONS_CARD}
    )
