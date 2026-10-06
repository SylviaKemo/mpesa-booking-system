from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.booking import AvailabilityOut, BookingCreate, BookingOut
from app.services.booking import BookingError, SlotUnavailable, availability, create_booking
from app.services.phone import InvalidPhoneNumber
from app.services.pricing import PricingError

router = APIRouter(tags=["bookings"])


@router.get("/availability", response_model=AvailabilityOut)
def get_availability(
    on: date = Query(alias="date", description="Day to check, as YYYY-MM-DD."),
    db: Session = Depends(get_db),
) -> AvailabilityOut:
    """Every slot for a day, each flagged free or taken."""
    return AvailabilityOut(date=on, slots=availability(db, on))


@router.post(
    "/bookings", response_model=BookingOut, status_code=status.HTTP_201_CREATED
)
def post_booking(payload: BookingCreate, db: Session = Depends(get_db)) -> BookingOut:
    """
    Create a booking.

    The request carries no money. Amount and deposit are computed from the
    catalogue rows the ids resolve to, then frozen onto the booking.
    """
    try:
        booking = create_booking(
            db,
            tier_id=payload.tier_id,
            addition_ids=payload.addition_ids,
            booking_date=payload.booking_date,
            slot_key=payload.slot_key,
            name=payload.name,
            phone=payload.phone,
            notes=payload.notes,
            payment_method=payload.payment_method,
        )
    except SlotUnavailable as exc:
        # 409: the request was valid, the world changed underneath it.
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except (PricingError, InvalidPhoneNumber, BookingError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    return BookingOut.model_validate(booking)
