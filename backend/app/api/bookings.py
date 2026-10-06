from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking, PaymentMethod
from app.schemas.booking import (
    AvailabilityOut,
    BookingCreate,
    BookingOut,
    BookingStatusOut,
)
from app.services.booking import BookingError, SlotUnavailable, availability, create_booking
from app.services.mpesa import get_provider
from app.services.payments import PaymentError, request_deposit
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

    if booking.payment_method is PaymentMethod.MPESA:
        try:
            request_deposit(db, booking, get_provider())
        except PaymentError as exc:
            # The booking stands and its hold still runs, so the client can be
            # prompted again rather than losing the slot to a provider outage.
            # The reference goes with the error: without it they hold a slot
            # they cannot poll for, and a retry collides with their own booking.
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                {
                    "message": "Your slot is held, but the M-Pesa request failed.",
                    "reference": booking.reference,
                    "reason": str(exc),
                },
            ) from exc
        db.refresh(booking)

    return BookingOut.model_validate(booking)


@router.get("/bookings/{reference}", response_model=BookingStatusOut)
def get_booking(reference: str, db: Session = Depends(get_db)) -> BookingStatusOut:
    """
    Look a booking up by its reference.

    An M-Pesa deposit confirms out of band, so the client polls this to learn
    when the prompt was answered.

    Returns no personal data. A reference is five characters and unauthenticated,
    so it is enumerable; the name, phone and notes behind one are not something a
    guess should buy.
    """
    booking = db.scalar(select(Booking).where(Booking.reference == reference))
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No booking with that reference.")

    return BookingStatusOut.model_validate(booking)
