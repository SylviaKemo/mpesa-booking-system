from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Addition, Booking, BookingStatus, PaymentMethod, Tier
from app.services.booking import (
    availability,
    create_booking,
    expire_stale_holds,
)


def _future_day(days: int = 3) -> date:
    return date.today() + timedelta(days=days)


def _payload(**overrides: object) -> dict:
    payload: dict = {
        "tier_id": "wispy-mid",
        "addition_ids": ["removal", "charms"],
        "booking_date": _future_day().isoformat(),
        "slot_key": "1430",
        "name": "Grace Mwangi",
        "phone": "0712 345 678",
        "notes": None,
        "payment_method": "studio",
    }
    payload.update(overrides)
    return payload


@pytest.mark.usefixtures("seeded")
def test_booking_is_priced_by_the_server(client: TestClient) -> None:
    body = client.post("/api/bookings", json=_payload()).json()

    assert body["amount_kes"] == 1100
    assert body["deposit_kes"] == 550
    assert body["minutes"] == 45


@pytest.mark.usefixtures("seeded")
def test_an_amount_sent_by_the_client_is_ignored(client: TestClient) -> None:
    """
    The whole point of pricing server-side: a tampered total must not be
    honoured. Extra fields are dropped and the catalogue still decides.
    """
    body = client.post(
        "/api/bookings",
        json=_payload(amount_kes=1, deposit_kes=1, minutes=1),
    ).json()

    assert body["amount_kes"] == 1100
    assert body["deposit_kes"] == 550


@pytest.mark.usefixtures("seeded")
def test_reference_is_server_generated_and_unambiguous(client: TestClient) -> None:
    reference = client.post("/api/bookings", json=_payload()).json()["reference"]

    assert reference.startswith("SS-")
    assert len(reference) == 8
    # No I, O, 0 or 1 — a reference gets read aloud down a phone.
    assert not set(reference[3:]) & set("IO01")


@pytest.mark.usefixtures("seeded")
def test_phone_is_stored_in_one_canonical_shape(client: TestClient) -> None:
    body = client.post("/api/bookings", json=_payload(phone="+254 712 345 678")).json()

    assert body["customer_phone"] == "254712345678"


@pytest.mark.usefixtures("seeded")
def test_studio_booking_is_confirmed_outright(client: TestClient) -> None:
    body = client.post("/api/bookings", json=_payload(payment_method="studio")).json()

    assert body["status"] == BookingStatus.CONFIRMED.value
    assert body["hold_expires_at"] is None


@pytest.mark.usefixtures("seeded")
def test_mpesa_booking_holds_the_slot_pending_payment(client: TestClient) -> None:
    body = client.post("/api/bookings", json=_payload(payment_method="mpesa")).json()

    assert body["status"] == BookingStatus.PENDING_PAYMENT.value
    assert body["hold_expires_at"] is not None


@pytest.mark.usefixtures("seeded")
def test_a_taken_slot_is_refused_with_conflict(client: TestClient) -> None:
    assert client.post("/api/bookings", json=_payload()).status_code == 201

    second = client.post("/api/bookings", json=_payload(name="Someone Else"))

    assert second.status_code == 409


@pytest.mark.usefixtures("seeded")
def test_a_pending_hold_also_blocks_the_slot(client: TestClient) -> None:
    """An unpaid hold occupies the slot; it is not free until it lapses."""
    client.post("/api/bookings", json=_payload(payment_method="mpesa"))

    second = client.post("/api/bookings", json=_payload(name="Someone Else"))

    assert second.status_code == 409


@pytest.mark.usefixtures("seeded")
def test_an_expired_hold_frees_the_slot(client: TestClient, db: Session) -> None:
    client.post("/api/bookings", json=_payload(payment_method="mpesa"))

    booking = db.query(Booking).one()
    booking.hold_expires_at = booking.hold_expires_at - timedelta(hours=1)
    db.commit()

    second = client.post("/api/bookings", json=_payload(name="Next Client"))

    assert second.status_code == 201


@pytest.mark.usefixtures("seeded")
def test_a_cancelled_booking_frees_the_slot(client: TestClient, db: Session) -> None:
    """
    The slot index is partial for this reason: a plain unique constraint would
    block the time forever once anyone had cancelled.
    """
    client.post("/api/bookings", json=_payload())

    db.query(Booking).one().status = BookingStatus.CANCELLED
    db.commit()

    assert client.post("/api/bookings", json=_payload()).status_code == 201


@pytest.mark.usefixtures("seeded")
def test_booking_a_past_date_is_refused(client: TestClient) -> None:
    response = client.post(
        "/api/bookings",
        json=_payload(booking_date=(date.today() - timedelta(days=1)).isoformat()),
    )

    assert response.status_code == 422


@pytest.mark.usefixtures("seeded")
def test_unknown_slot_is_refused(client: TestClient) -> None:
    response = client.post("/api/bookings", json=_payload(slot_key="0300"))

    assert response.status_code == 422


@pytest.mark.usefixtures("seeded")
def test_unreachable_phone_is_refused(client: TestClient) -> None:
    response = client.post("/api/bookings", json=_payload(phone="0812345678"))

    assert response.status_code == 422


@pytest.mark.usefixtures("seeded")
def test_blank_name_is_refused(client: TestClient) -> None:
    response = client.post("/api/bookings", json=_payload(name="   "))

    assert response.status_code == 422


@pytest.mark.usefixtures("seeded")
def test_additions_are_frozen_at_the_price_charged(
    client: TestClient, db: Session
) -> None:
    """A later price rise must not rewrite a booking already agreed."""
    client.post("/api/bookings", json=_payload())

    db.get(Addition, "removal").amount_kes = 9999
    db.commit()

    booking = db.query(Booking).one()
    charged = {a.addition_id: a.amount_kes for a in booking.additions}

    assert charged["removal"] == 300
    assert booking.amount_kes == 1100


@pytest.mark.usefixtures("seeded")
def test_availability_marks_a_taken_slot(client: TestClient) -> None:
    day = _future_day()
    client.post("/api/bookings", json=_payload())

    body = client.get("/api/availability", params={"date": day.isoformat()}).json()
    slots = {s["key"]: s["available"] for s in body["slots"]}

    assert slots["1430"] is False
    assert slots["0900"] is True
    assert len(slots) == 8


@pytest.mark.usefixtures("seeded")
def test_availability_offers_nothing_on_a_past_day(client: TestClient) -> None:
    past = (date.today() - timedelta(days=1)).isoformat()

    body = client.get("/api/availability", params={"date": past}).json()

    assert all(slot["available"] is False for slot in body["slots"])


@pytest.mark.usefixtures("seeded")
def test_expire_stale_holds_only_touches_lapsed_pending_bookings(db: Session) -> None:
    day = _future_day()
    held = create_booking(
        db,
        tier_id="wispy-mid",
        addition_ids=[],
        booking_date=day,
        slot_key="0900",
        name="A",
        phone="0712345678",
        notes=None,
        payment_method=PaymentMethod.MPESA,
    )
    confirmed = create_booking(
        db,
        tier_id="wispy-mid",
        addition_ids=[],
        booking_date=day,
        slot_key="1000",
        name="B",
        phone="0712345679",
        notes=None,
        payment_method=PaymentMethod.STUDIO,
    )
    held.hold_expires_at = held.hold_expires_at - timedelta(hours=1)
    db.commit()

    released = expire_stale_holds(db)
    db.commit()

    db.refresh(held)
    db.refresh(confirmed)
    assert released == 1
    assert held.status == BookingStatus.EXPIRED
    assert confirmed.status == BookingStatus.CONFIRMED

    free = {slot.key: slot.available for slot in availability(db, day)}
    assert free["0900"] is True
    assert free["1000"] is False


@pytest.mark.usefixtures("seeded")
def test_same_slot_on_a_different_day_is_bookable(client: TestClient) -> None:
    client.post("/api/bookings", json=_payload())

    other_day = _future_day(4).isoformat()
    second = client.post("/api/bookings", json=_payload(booking_date=other_day))

    assert second.status_code == 201


@pytest.mark.usefixtures("seeded")
def test_withdrawn_tier_cannot_be_booked(client: TestClient, db: Session) -> None:
    db.get(Tier, "wispy-mid").is_active = False
    db.commit()

    assert client.post("/api/bookings", json=_payload()).status_code == 422


@pytest.mark.usefixtures("seeded")
def test_booking_without_additions_prices_the_tier_alone(client: TestClient) -> None:
    body = client.post("/api/bookings", json=_payload(addition_ids=[])).json()

    assert body["amount_kes"] == 700
    assert body["deposit_kes"] == 350
    assert body["additions"] == []
