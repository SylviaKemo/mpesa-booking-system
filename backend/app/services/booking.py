"""Availability and booking creation."""

import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    BLOCKING_STATUSES,
    Booking,
    BookingAddition,
    BookingStatus,
    PaymentMethod,
)
from app.config import get_settings
from app.services.phone import normalise
from app.services.pricing import Quote, quote
from app.slots import SLOTS, get_slot, starts_at

#: How long a slot is held while an M-Pesa deposit is confirmed. Long enough to
#: re-enter a PIN, short enough that an abandoned attempt frees the slot.
HOLD_MINUTES = 15

_REFERENCE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_REFERENCE_ATTEMPTS = 5


class BookingError(Exception):
    """The booking cannot be made as asked."""


class SlotUnavailable(BookingError):
    """Someone else holds the slot."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _salon_now() -> datetime:
    """
    Now, on the salon's wall clock.

    Whether a slot has passed is a question about Nairobi, not about wherever
    the server happens to run.
    """
    return datetime.now(get_settings().tz)


def _slot_has_passed(on: date, slot_key: str, now: datetime) -> bool:
    slot = get_slot(slot_key)
    if slot is None:
        return True
    return starts_at(slot, on, get_settings().tz) <= now


def _last_bookable_day(now: datetime) -> date:
    return now.date() + timedelta(days=get_settings().max_booking_lead_days)


def _make_reference() -> str:
    """
    "SS-" plus five characters, matching what the prototype showed clients.

    Drawn from an alphabet without I, O, 0 or 1 so a reference read aloud or
    copied off a screen is unambiguous.
    """
    body = "".join(secrets.choice(_REFERENCE_ALPHABET) for _ in range(5))
    return f"SS-{body}"


def _slot_is_taken(db: Session, on: date, slot_key: str) -> bool:
    return (
        db.scalar(
            select(Booking.id).where(
                Booking.booking_date == on,
                Booking.slot_key == slot_key,
                Booking.status.in_(BLOCKING_STATUSES),
            )
        )
        is not None
    )


def _is_reference_conflict(exc: IntegrityError) -> bool:
    """
    Whether a failed insert clashed on the reference.

    Dialects word this differently — SQLite names the column, Postgres the
    constraint — so both spellings are checked rather than assuming one.
    """
    message = str(exc.orig).lower()
    return "reference" in message


def expire_stale_holds(db: Session) -> int:
    """
    Release holds whose payment never arrived.

    Called before reading or writing availability rather than from a scheduler:
    with no background worker, lazily expiring on access keeps a lapsed hold
    from blocking a slot indefinitely. Returns how many were released.
    """
    result = db.execute(
        update(Booking)
        .where(
            Booking.status == BookingStatus.PENDING_PAYMENT,
            Booking.hold_expires_at.is_not(None),
            Booking.hold_expires_at < _now(),
        )
        .values(status=BookingStatus.EXPIRED, hold_expires_at=None)
    )
    return result.rowcount or 0


@dataclass(frozen=True)
class SlotAvailability:
    key: str
    label: str
    available: bool


def availability(
    db: Session, on: date, now: datetime | None = None
) -> list[SlotAvailability]:
    """
    Every slot for a day, flagged free or taken.

    The whole day is returned rather than only free slots, so the client can
    show a taken time as disabled instead of silently omitting it.

    `now` is the single clock these decisions are made against; callers that
    need a deterministic answer pass it, and it reaches every guard.
    """
    expire_stale_holds(db)
    db.commit()

    taken = set(
        db.scalars(
            select(Booking.slot_key).where(
                Booking.booking_date == on,
                Booking.status.in_(BLOCKING_STATUSES),
            )
        ).all()
    )

    moment = now or _salon_now()

    # Beyond the lead time nothing is bookable, and saying otherwise would have
    # this endpoint offer slots that POST /api/bookings then refuses.
    too_far = on > _last_bookable_day(moment)

    return [
        SlotAvailability(
            key=slot.key,
            label=slot.label,
            available=(
                not too_far
                and slot.key not in taken
                # Comparing whole days would leave this morning's slots on offer
                # all afternoon, so each is judged against its own start time.
                and starts_at(slot, on, get_settings().tz) > moment
            ),
        )
        for slot in SLOTS
    ]


def create_booking(
    db: Session,
    *,
    tier_id: str,
    addition_ids: list[str],
    booking_date: date,
    slot_key: str,
    name: str,
    phone: str,
    notes: str | None,
    payment_method: PaymentMethod,
    now: datetime | None = None,
) -> Booking:
    """
    Create a booking, pricing it from the catalogue.

    Nothing monetary comes from the caller: the amount and deposit are computed
    from the tier and addition ids against the catalogue, then frozen onto the
    row so a later price change cannot alter an agreed booking.
    """
    if get_slot(slot_key) is None:
        raise BookingError(f"Unknown time slot: {slot_key!r}")

    moment = now or _salon_now()

    if booking_date > _last_bookable_day(moment):
        raise BookingError(
            f"Bookings open {get_settings().max_booking_lead_days} days ahead. "
            "Please choose an earlier date."
        )

    if _slot_has_passed(booking_date, slot_key, moment):
        raise BookingError("That time has already passed. Please choose another.")

    customer_name = (name or "").strip()
    if not customer_name:
        raise BookingError("A name is required.")

    customer_phone = normalise(phone)

    priced: Quote = quote(db, tier_id, addition_ids)

    expire_stale_holds(db)

    # Cheap check for the ordinary case. The unique index below is what actually
    # makes this safe; this only turns the common miss into a clean answer
    # without burning a reference.
    if _slot_is_taken(db, booking_date, slot_key):
        raise SlotUnavailable("That time has just been taken. Please choose another.")

    if payment_method is PaymentMethod.MPESA:
        status = BookingStatus.PENDING_PAYMENT
        hold_expires_at = _now() + timedelta(minutes=HOLD_MINUTES)
    else:
        # Paying at the studio settles on arrival, so the slot is held outright.
        status = BookingStatus.CONFIRMED
        hold_expires_at = None

    for _ in range(_REFERENCE_ATTEMPTS):
        booking = Booking(
            reference=_make_reference(),
            booking_date=booking_date,
            slot_key=slot_key,
            status=status,
            payment_method=payment_method,
            tier_id=priced.tier.id,
            amount_kes=priced.amount_kes,
            deposit_kes=priced.deposit_kes,
            minutes=priced.minutes,
            customer_name=customer_name,
            customer_phone=customer_phone,
            notes=(notes or "").strip() or None,
            hold_expires_at=hold_expires_at,
        )
        booking.additions = [
            BookingAddition(
                addition_id=addition.id,
                amount_kes=addition.amount_kes,
                minutes=addition.minutes,
            )
            for addition in priced.additions
        ]

        db.add(booking)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            # Two constraints can fire: the slot index, meaning someone booked
            # between the check above and this insert, and the reference index,
            # which is a collision worth retrying. The driver's message names
            # them differently per dialect — SQLite lists columns, Postgres the
            # index — so ask the database which is true instead of parsing text.
            if _slot_is_taken(db, booking_date, slot_key):
                raise SlotUnavailable(
                    "That time has just been taken. Please choose another."
                ) from exc

            # Only a reference clash is worth another go. Anything else — a
            # foreign key, a check constraint — will fail identically five more
            # times and then be reported as a reference problem, sending whoever
            # debugs it to the wrong place.
            if not _is_reference_conflict(exc):
                raise
            continue

        db.refresh(booking)
        return booking

    raise BookingError("Could not allocate a booking reference. Please try again.")
