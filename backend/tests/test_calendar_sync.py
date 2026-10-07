"""
Confirmed bookings reaching Shamim's calendar.

The calendar is her only view of bookings, so what matters is that every
confirmed booking lands there exactly once, and that a calendar outage neither
undoes a booking nor loses it.
"""

import re
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus, Payment
from app.services.calendar import CalendarError, FakeCalendarProvider, sync_confirmed_bookings

SECRET = "test-callback-secret"
NAIROBI = ZoneInfo("Africa/Nairobi")


def _day(days: int = 3) -> date:
    return date.today() + timedelta(days=days)


def _payload(**overrides: object) -> dict:
    payload: dict = {
        "tier_id": "wispy-mid",
        "addition_ids": ["removal"],
        "booking_date": _day().isoformat(),
        "slot_key": "1430",
        "name": "Grace Mwangi",
        "phone": "0712 345 678",
        "notes": "Sensitive eyes",
        "payment_method": "studio",
    }
    payload.update(overrides)
    return payload


def _confirm(client: TestClient, db: Session, *, result_code: int = 0) -> Any:
    """Book by M-Pesa and answer the prompt the way Safaricom would."""
    created = client.post("/api/bookings", json=_payload(payment_method="mpesa")).json()
    payment = db.query(Payment).filter_by(amount_kes=created["deposit_kes"]).one()
    callback: dict[str, Any] = {
        "CheckoutRequestID": payment.checkout_request_id,
        "ResultCode": result_code,
        "ResultDesc": "ok" if result_code == 0 else "Request cancelled by user",
    }
    if result_code == 0:
        callback["CallbackMetadata"] = {
            "Item": [
                {"Name": "Amount", "Value": created["deposit_kes"]},
                {"Name": "MpesaReceiptNumber", "Value": "SGH3RTY89K"},
            ]
        }
    body = {"Body": {"stkCallback": callback}}
    return client.post(f"/api/mpesa/callback/{SECRET}", json=body), body


@pytest.mark.usefixtures("seeded")
def test_a_studio_booking_goes_straight_into_the_calendar(
    client: TestClient, db: Session, calendar: FakeCalendarProvider
) -> None:
    created = client.post("/api/bookings", json=_payload()).json()

    assert len(calendar.events) == 1
    event = calendar.events[0]

    # The slot on the salon's clock, for as long as the booking takes.
    assert event.start == datetime.combine(_day(), datetime.min.time(), NAIROBI).replace(
        hour=14, minute=30
    )
    assert event.end - event.start == timedelta(minutes=created["minutes"])
    assert event.timezone == "Africa/Nairobi"

    assert event.summary == "Grace Mwangi · Wispy set, Mid volume"
    assert created["reference"] in event.description
    assert "+254712345678" in event.description
    assert "+ Removal" in event.description
    assert "Pays at the studio: KES 1,000" in event.description
    assert "Notes: Sensitive eyes" in event.description

    db.expire_all()
    assert db.query(Booking).one().calendar_synced_at is not None


@pytest.mark.usefixtures("seeded")
def test_an_mpesa_booking_waits_for_its_deposit(
    client: TestClient, db: Session, calendar: FakeCalendarProvider
) -> None:
    """A held slot may never be paid for; Shamim should not plan around it."""
    client.post("/api/bookings", json=_payload(payment_method="mpesa"))

    assert calendar.events == []


@pytest.mark.usefixtures("seeded")
def test_a_paid_deposit_puts_the_booking_in_the_calendar(
    client: TestClient, db: Session, calendar: FakeCalendarProvider
) -> None:
    response, _ = _confirm(client, db)

    assert response.status_code == 200
    assert len(calendar.events) == 1
    description = calendar.events[0].description
    # The receipt lets her match the booking to her M-Pesa statement.
    assert "Deposit paid by M-Pesa: KES 500 (SGH3RTY89K)" in description
    assert "Balance due: KES 500" in description


@pytest.mark.usefixtures("seeded")
def test_a_retried_confirmation_adds_the_booking_once(
    client: TestClient, db: Session, calendar: FakeCalendarProvider
) -> None:
    _, body = _confirm(client, db)
    client.post(f"/api/mpesa/callback/{SECRET}", json=body)

    assert len(calendar.events) == 1


@pytest.mark.usefixtures("seeded")
def test_a_failed_payment_stays_out_of_the_calendar(
    client: TestClient, db: Session, calendar: FakeCalendarProvider
) -> None:
    _confirm(client, db, result_code=1032)

    assert calendar.events == []


@pytest.mark.usefixtures("seeded")
def test_a_calendar_outage_does_not_undo_the_payment(
    client: TestClient, db: Session, calendar: FakeCalendarProvider
) -> None:
    """
    The money moved and the slot is the client's whatever Google says. Failing
    the callback would only make Safaricom retry a payment already settled.
    """
    calendar.fail_with = CalendarError("Google Calendar rejected the event (503)")

    response, _ = _confirm(client, db)

    assert response.status_code == 200
    assert response.json()["ResultCode"] == 0
    db.expire_all()
    booking = db.query(Booking).one()
    assert booking.status is BookingStatus.CONFIRMED
    assert booking.calendar_synced_at is None


@pytest.mark.usefixtures("seeded")
def test_the_next_booking_catches_up_what_an_outage_missed(
    client: TestClient, db: Session, calendar: FakeCalendarProvider
) -> None:
    calendar.fail_with = CalendarError("Google Calendar rejected the event (503)")
    _confirm(client, db)
    assert calendar.events == []

    calendar.fail_with = None
    client.post("/api/bookings", json=_payload(slot_key="0900", name="Amina Otieno"))

    assert sorted(event.summary.split(" · ")[0] for event in calendar.events) == [
        "Amina Otieno",
        "Grace Mwangi",
    ]
    db.expire_all()
    assert all(b.calendar_synced_at is not None for b in db.query(Booking).all())


@pytest.mark.usefixtures("seeded")
def test_the_sweep_is_safe_to_rerun(
    client: TestClient, db: Session, calendar: FakeCalendarProvider
) -> None:
    client.post("/api/bookings", json=_payload())

    assert sync_confirmed_bookings(db, calendar) == 0
    assert len(calendar.events) == 1


@pytest.mark.usefixtures("seeded")
def test_appointments_already_past_are_not_backfilled(
    client: TestClient, db: Session, calendar: FakeCalendarProvider
) -> None:
    """The first sync after deploy should bring her upcoming week, not her history."""
    calendar.fail_with = CalendarError("down")
    client.post("/api/bookings", json=_payload())
    calendar.fail_with = None

    assert sync_confirmed_bookings(db, calendar, today=_day(4)) == 0
    assert calendar.events == []


@pytest.mark.usefixtures("seeded")
def test_event_ids_are_ones_google_accepts(
    client: TestClient, calendar: FakeCalendarProvider
) -> None:
    """
    Google allows only a–v and 0–9, five to 1024 of them. A reference such as
    SS-4KD9P has a hyphen and letters past v, so it cannot be used as is.
    """
    client.post("/api/bookings", json=_payload())

    assert re.fullmatch(r"[a-v0-9]{5,1024}", calendar.events[0].event_id)
