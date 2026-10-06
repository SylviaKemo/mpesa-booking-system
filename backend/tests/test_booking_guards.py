"""Guards around when a booking may be made, and how conflicts are reported."""

from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import engine
from app.models import LIVE_BOOKING_PREDICATE, PaymentMethod
from app.services.booking import BookingError, availability, create_booking
from app.slots import SLOTS, starts_at


def _payload(**overrides: object) -> dict:
    payload: dict = {
        "tier_id": "wispy-mid",
        "addition_ids": [],
        "booking_date": (date.today() + timedelta(days=2)).isoformat(),
        "slot_key": "1430",
        "name": "Grace Mwangi",
        "phone": "0712345678",
        "notes": None,
        "payment_method": "studio",
    }
    payload.update(overrides)
    return payload


@pytest.mark.usefixtures("seeded")
def test_a_slot_earlier_today_cannot_be_booked(db: Session) -> None:
    """
    Comparing whole days left this morning's slots on offer all afternoon, so a
    client could book 9:00 am at 5:00 pm the same day.
    """
    tz = get_settings().tz
    now = datetime.now(tz)
    today = now.date()

    with pytest.raises(BookingError, match="already passed"):
        create_booking(
            db,
            tier_id="wispy-mid",
            addition_ids=[],
            booking_date=today,
            slot_key="0900",
            name="Late Client",
            phone="0712345678",
            notes=None,
            payment_method=PaymentMethod.STUDIO,
            now=now,
        )


@pytest.mark.usefixtures("seeded")
def test_availability_hides_slots_that_have_started(db: Session) -> None:
    tz = get_settings().tz
    now = datetime.now(tz)
    today = now.date()

    offered = {slot.key: slot.available for slot in availability(db, today)}

    for slot in SLOTS:
        already_started = starts_at(slot, today, tz) <= now
        assert offered[slot.key] is not already_started, slot.key


@pytest.mark.usefixtures("seeded")
def test_a_slot_later_today_is_still_bookable(db: Session) -> None:
    """Only passed slots go; the rest of today must stay open."""
    tz = get_settings().tz
    now = datetime.now(tz)
    today = now.date()

    remaining = [s for s in SLOTS if starts_at(s, today, tz) > now]
    if not remaining:
        pytest.skip("no slots left today to exercise this")

    booking = create_booking(
        db,
        tier_id="wispy-mid",
        addition_ids=[],
        booking_date=today,
        slot_key=remaining[0].key,
        name="In Time",
        phone="0712345678",
        notes=None,
        payment_method=PaymentMethod.STUDIO,
        now=now,
    )

    assert booking.reference.startswith("SS-")


@pytest.mark.usefixtures("seeded")
def test_booking_beyond_the_lead_time_is_refused(client: TestClient) -> None:
    """
    A confirmed booking holds its slot and nothing reaps it, so without a bound
    the whole calendar could be taken years out.
    """
    settings = get_settings()
    too_far = date.today() + timedelta(days=settings.max_booking_lead_days + 1)

    response = client.post("/api/bookings", json=_payload(booking_date=too_far.isoformat()))

    assert response.status_code == 422
    assert "days ahead" in response.json()["detail"]


@pytest.mark.usefixtures("seeded")
def test_booking_at_the_edge_of_the_lead_time_is_allowed(client: TestClient) -> None:
    settings = get_settings()
    edge = date.today() + timedelta(days=settings.max_booking_lead_days)

    response = client.post("/api/bookings", json=_payload(booking_date=edge.isoformat()))

    assert response.status_code == 201


def test_slot_times_are_the_salon_wall_clock() -> None:
    """
    Slot times are Nairobi's, not the server's. A deployment running UTC would
    otherwise treat a finished day as bookable for three hours every night.
    """
    tz = get_settings().tz
    moment = starts_at(SLOTS[0], date(2026, 10, 6), tz)

    assert moment.timetz().replace(tzinfo=None) == time(9, 0)
    assert moment.utcoffset() == timedelta(hours=3)


def test_the_live_slot_index_still_matches_blocking_statuses() -> None:
    """
    The index predicate is derived from BLOCKING_STATUSES, but the migration
    holds a snapshot. Adding a status without a migration would leave the
    database enforcing less than the code believes, so the two are compared.
    """
    indexes = inspect(engine).get_indexes("bookings")
    live = next(i for i in indexes if i["name"] == "uq_bookings_live_slot")

    predicate = (live.get("dialect_options") or {}).get("sqlite_where")
    assert predicate is not None, "slot index lost its partial predicate"
    assert str(predicate) == LIVE_BOOKING_PREDICATE


@pytest.mark.usefixtures("seeded")
def test_availability_offers_nothing_beyond_the_lead_time(
    client: TestClient, db: Session
) -> None:
    """
    Availability and booking must agree. Offering a slot the POST then refuses
    lets a client pick a time, fill the form, and only then be turned away.
    """
    settings = get_settings()
    too_far = date.today() + timedelta(days=settings.max_booking_lead_days + 1)

    offered = availability(db, too_far)
    assert all(slot.available is False for slot in offered)

    rejected = client.post("/api/bookings", json=_payload(booking_date=too_far.isoformat()))
    assert rejected.status_code == 422


@pytest.mark.usefixtures("seeded")
def test_the_injected_clock_reaches_every_guard(db: Session) -> None:
    """
    A pinned `now` must decide both the lead bound and whether a slot has
    started; honouring it in one and not the other makes results depend on the
    wall clock despite the caller pinning it.
    """
    tz = get_settings().tz
    # Late evening: every slot that day has started.
    evening = datetime.combine(date(2026, 10, 6), time(23, 0), tzinfo=tz)

    offered = availability(db, evening.date(), now=evening)
    assert all(slot.available is False for slot in offered)

    with pytest.raises(BookingError, match="already passed"):
        create_booking(
            db,
            tier_id="wispy-mid",
            addition_ids=[],
            booking_date=evening.date(),
            slot_key="1800",
            name="Too Late",
            phone="0712345678",
            notes=None,
            payment_method=PaymentMethod.STUDIO,
            now=evening,
        )

    # Early morning on the same day: everything is still ahead.
    morning = datetime.combine(date(2026, 10, 6), time(6, 0), tzinfo=tz)
    assert all(slot.available for slot in availability(db, morning.date(), now=morning))


@pytest.mark.usefixtures("seeded")
def test_status_and_payment_method_round_trip_as_enums(
    client: TestClient, db: Session
) -> None:
    """
    A String column annotated as an enum returns str, so `.value` raises while a
    type checker accepts it — the kind of thing that only fails on real data.
    """
    from app.models import Booking, BookingStatus, PaymentMethod as PM

    client.post("/api/bookings", json=_payload(payment_method="mpesa"))
    db.expire_all()

    booking = db.query(Booking).one()

    assert isinstance(booking.status, BookingStatus)
    assert isinstance(booking.payment_method, PM)
    assert booking.status.value == "pending_payment"
    assert booking.payment_method.value == "mpesa"
