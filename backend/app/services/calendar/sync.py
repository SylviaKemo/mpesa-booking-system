"""
Putting confirmed bookings in Shamim's calendar.

The calendar is her only view of bookings, so a confirmation that never reaches
it is a client she does not know is coming. Two rules follow.

A calendar outage must not undo a booking: the slot and the client's money are
settled before this runs, and nothing here can roll them back.

A miss must be retried: rather than syncing one booking, every run sweeps all
confirmed bookings not yet in the calendar, so the next confirmation — or the
sync command — picks up whatever an earlier outage left behind.
"""

import base64
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import Booking, BookingStatus, PaymentMethod, PaymentStatus
from app.services.calendar.base import CalendarError, CalendarEvent, CalendarProvider
from app.services.calendar.registry import get_calendar
from app.slots import get_slot, starts_at

logger = logging.getLogger(__name__)


def _event_id(reference: str) -> str:
    """
    A Google-legal event id derived from the booking reference.

    Google accepts only a–v and 0–9, which is exactly lower-case base32hex. The
    same reference always gives the same id, which is what makes a retried
    insert a no-op rather than a second event.
    """
    encoded = base64.b32hexencode(f"shamim{reference}".encode()).decode()
    return encoded.rstrip("=").lower()


def _money(kes: int) -> str:
    return f"KES {kes:,}"


def _payment_lines(booking: Booking) -> list[str]:
    if booking.payment_method is PaymentMethod.STUDIO:
        return [f"Pays at the studio: {_money(booking.amount_kes)}"]

    receipt = next(
        (
            payment.mpesa_receipt
            for payment in booking.payments
            if payment.status is PaymentStatus.SUCCEEDED
        ),
        None,
    )
    deposit = f"Deposit paid by M-Pesa: {_money(booking.deposit_kes)}"
    if receipt:
        deposit += f" ({receipt})"
    return [
        deposit,
        f"Balance due: {_money(booking.amount_kes - booking.deposit_kes)}",
    ]


def event_for(booking: Booking) -> CalendarEvent:
    """
    The calendar entry for a booking.

    Written for Shamim reading it on her phone: who, what, and what money is
    still owed, with the reference to match it to an M-Pesa statement.
    """
    slot = get_slot(booking.slot_key)
    if slot is None:
        # Bookings are validated against SLOTS, so this means a slot was
        # removed from the code while bookings for it still exist.
        raise CalendarError(f"Booking {booking.reference} has unknown slot {booking.slot_key!r}")

    settings = get_settings()
    start = starts_at(slot, booking.booking_date, settings.tz)
    end = start + timedelta(minutes=booking.minutes)

    tier = booking.tier
    service = f"{tier.lash_set.name}, {tier.label}"

    lines = [
        f"Booking {booking.reference}",
        f"Phone: +{booking.customer_phone}",
        "",
        service,
        *(f"+ {item.addition.label}" for item in booking.additions),
        "",
        f"Total: {_money(booking.amount_kes)}",
        *_payment_lines(booking),
    ]
    if booking.notes:
        lines += ["", f"Notes: {booking.notes}"]

    return CalendarEvent(
        event_id=_event_id(booking.reference),
        summary=f"{booking.customer_name} · {service}",
        description="\n".join(lines),
        start=start,
        end=end,
        timezone=settings.salon_timezone,
    )


def sync_confirmed_bookings(
    db: Session, calendar: CalendarProvider, *, today: date | None = None
) -> int:
    """
    Add every confirmed booking the calendar is missing. Returns how many.

    Bookings already past are skipped: an appointment that has happened is no
    use in a calendar, and the first run after deploy would otherwise backfill
    the whole history.

    Each booking is committed as it lands, so a failure part way through keeps
    the ones that made it. A failure is logged and the sweep moves on — one bad
    booking must not hold back the rest.
    """
    today = today or datetime.now(get_settings().tz).date()

    pending = db.scalars(
        select(Booking)
        .where(
            Booking.status == BookingStatus.CONFIRMED,
            Booking.calendar_synced_at.is_(None),
            Booking.booking_date >= today,
        )
        .order_by(Booking.booking_date, Booking.slot_key)
    ).all()

    synced = 0
    for booking in pending:
        try:
            calendar.add_event(event_for(booking))
        except CalendarError as exc:
            # The reference only: the event carries the client's name and
            # phone, and those have no business in a log.
            logger.error(
                "Booking %s is not in the calendar yet: %s", booking.reference, exc
            )
            continue

        booking.calendar_synced_at = datetime.now(timezone.utc)
        db.commit()
        synced += 1

    return synced


def sync_in_background() -> None:
    """
    The sweep, for a background task queued by a request that confirmed a booking.

    Opens its own session: by the time a background task runs, the request's
    session has been closed.
    """
    with SessionLocal() as db:
        sync_confirmed_bookings(db, get_calendar())
