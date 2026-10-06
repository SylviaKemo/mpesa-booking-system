from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus, Payment, PaymentStatus
from app.services.mpesa import FakeMpesaProvider, MpesaError

SECRET = "test-callback-secret"


def _payload(**overrides: object) -> dict:
    payload: dict = {
        "tier_id": "wispy-mid",
        "addition_ids": ["removal"],
        "booking_date": (date.today() + timedelta(days=3)).isoformat(),
        "slot_key": "1430",
        "name": "Grace Mwangi",
        "phone": "0712 345 678",
        "notes": None,
        "payment_method": "mpesa",
    }
    payload.update(overrides)
    return payload


def _callback(
    checkout_request_id: str,
    *,
    result_code: int = 0,
    amount: int | None = None,
    receipt: str = "SGH3RTY89K",
) -> dict[str, Any]:
    """Safaricom's callback envelope, as it actually arrives."""
    callback: dict[str, Any] = {
        "MerchantRequestID": "fake-merchant-1",
        "CheckoutRequestID": checkout_request_id,
        "ResultCode": result_code,
        "ResultDesc": "The service request is processed successfully."
        if result_code == 0
        else "Request cancelled by user",
    }
    if result_code == 0:
        callback["CallbackMetadata"] = {
            "Item": [
                {"Name": "Amount", "Value": amount},
                {"Name": "MpesaReceiptNumber", "Value": receipt},
                {"Name": "PhoneNumber", "Value": 254712345678},
            ]
        }
    return {"Body": {"stkCallback": callback}}


def _post_callback(client: TestClient, payload: dict, secret: str = SECRET):
    return client.post(f"/api/mpesa/callback/{secret}", json=payload)


@pytest.mark.usefixtures("seeded")
def test_mpesa_booking_sends_a_prompt_for_the_deposit(
    client: TestClient, mpesa: FakeMpesaProvider
) -> None:
    body = client.post("/api/bookings", json=_payload()).json()

    assert len(mpesa.sent) == 1
    sent = mpesa.sent[0]
    # The amount is the server's deposit, never anything the client supplied.
    assert sent.amount_kes == body["deposit_kes"] == 500
    assert sent.phone == "254712345678"
    assert sent.account_reference == body["reference"]


@pytest.mark.usefixtures("seeded")
def test_studio_booking_sends_no_prompt(
    client: TestClient, mpesa: FakeMpesaProvider
) -> None:
    client.post("/api/bookings", json=_payload(payment_method="studio"))

    assert mpesa.sent == []


@pytest.mark.usefixtures("seeded")
def test_a_successful_callback_confirms_the_booking(
    client: TestClient, db: Session
) -> None:
    created = client.post("/api/bookings", json=_payload()).json()
    payment = db.query(Payment).one()

    response = _post_callback(
        client, _callback(payment.checkout_request_id, amount=created["deposit_kes"])
    )

    assert response.status_code == 200
    db.expire_all()
    booking = db.query(Booking).one()
    assert booking.status is BookingStatus.CONFIRMED
    # The hold has done its job; the slot is the client's outright.
    assert booking.hold_expires_at is None
    assert db.query(Payment).one().status is PaymentStatus.SUCCEEDED
    assert db.query(Payment).one().mpesa_receipt == "SGH3RTY89K"


@pytest.mark.usefixtures("seeded")
def test_a_repeated_callback_settles_the_booking_only_once(
    client: TestClient, db: Session
) -> None:
    """Safaricom retries until it gets a 200, so the same confirmation arrives again."""
    created = client.post("/api/bookings", json=_payload()).json()
    payment = db.query(Payment).one()
    body = _callback(payment.checkout_request_id, amount=created["deposit_kes"])

    first = _post_callback(client, body)
    second = _post_callback(client, body)

    assert first.status_code == second.status_code == 200
    db.expire_all()
    assert db.query(Payment).count() == 1
    assert db.query(Booking).one().status is BookingStatus.CONFIRMED


@pytest.mark.usefixtures("seeded")
def test_a_cancelled_payment_leaves_the_booking_pending(
    client: TestClient, db: Session
) -> None:
    """
    The hold is not torn down on failure: it lapses on its own, and until then
    the client can answer a fresh prompt without losing the slot.
    """
    client.post("/api/bookings", json=_payload())
    payment = db.query(Payment).one()

    _post_callback(client, _callback(payment.checkout_request_id, result_code=1032))

    db.expire_all()
    assert db.query(Payment).one().status is PaymentStatus.FAILED
    booking = db.query(Booking).one()
    assert booking.status is BookingStatus.PENDING_PAYMENT
    assert booking.hold_expires_at is not None


@pytest.mark.usefixtures("seeded")
def test_a_callback_claiming_the_wrong_amount_does_not_confirm(
    client: TestClient, db: Session
) -> None:
    """
    Safaricom does not sign callbacks, so the amount is checked against what we
    asked for. Believing the payload would confirm a booking nobody paid for.
    """
    client.post("/api/bookings", json=_payload())
    payment = db.query(Payment).one()

    response = _post_callback(
        client, _callback(payment.checkout_request_id, amount=1)
    )

    assert response.status_code == 200
    db.expire_all()
    assert db.query(Payment).one().status is PaymentStatus.FAILED
    assert db.query(Booking).one().status is BookingStatus.PENDING_PAYMENT


@pytest.mark.usefixtures("seeded")
def test_a_callback_with_a_bad_secret_is_not_found(
    client: TestClient, db: Session
) -> None:
    """The secret in the path is the only thing standing in for a signature."""
    client.post("/api/bookings", json=_payload())
    payment = db.query(Payment).one()

    response = _post_callback(
        client, _callback(payment.checkout_request_id, amount=500), secret="guessed"
    )

    assert response.status_code == 404
    db.expire_all()
    assert db.query(Booking).one().status is BookingStatus.PENDING_PAYMENT


@pytest.mark.usefixtures("seeded")
def test_a_callback_for_an_unknown_payment_is_accepted_but_changes_nothing(
    client: TestClient, db: Session
) -> None:
    """Answering 200 stops Safaricom retrying something that will never match."""
    client.post("/api/bookings", json=_payload())

    response = _post_callback(client, _callback("ws_CO_not_ours", amount=500))

    assert response.status_code == 200
    db.expire_all()
    assert db.query(Booking).one().status is BookingStatus.PENDING_PAYMENT


@pytest.mark.usefixtures("seeded")
def test_a_malformed_callback_is_accepted_without_raising(client: TestClient) -> None:
    """It will stay malformed, so a retry helps nobody."""
    response = _post_callback(client, {"Body": {"stkCallback": {}}})

    assert response.status_code == 200


@pytest.mark.usefixtures("seeded")
def test_a_provider_outage_keeps_the_booking_and_its_hold(
    client: TestClient, db: Session, mpesa: FakeMpesaProvider
) -> None:
    """
    The slot stays held so the client can be prompted again, rather than losing
    it because Safaricom was briefly unreachable.
    """
    mpesa.fail_with = MpesaError("Daraja unavailable")

    response = client.post("/api/bookings", json=_payload())

    assert response.status_code == 502
    booking = db.query(Booking).one()
    assert booking.status is BookingStatus.PENDING_PAYMENT
    assert booking.hold_expires_at is not None
    assert db.query(Payment).count() == 0


@pytest.mark.usefixtures("seeded")
def test_a_booking_can_be_polled_by_reference(client: TestClient, db: Session) -> None:
    """The deposit confirms out of band, so the client polls to learn when."""
    created = client.post("/api/bookings", json=_payload()).json()
    reference = created["reference"]

    before = client.get(f"/api/bookings/{reference}").json()
    assert before["status"] == BookingStatus.PENDING_PAYMENT.value
    assert before["payments"][0]["status"] == PaymentStatus.PENDING.value

    payment = db.query(Payment).one()
    _post_callback(client, _callback(payment.checkout_request_id, amount=created["deposit_kes"]))

    after = client.get(f"/api/bookings/{reference}").json()
    assert after["status"] == BookingStatus.CONFIRMED.value
    assert after["payments"][0]["status"] == PaymentStatus.SUCCEEDED.value
    assert after["payments"][0]["mpesa_receipt"] == "SGH3RTY89K"


def test_an_unknown_reference_is_not_found(client: TestClient) -> None:
    assert client.get("/api/bookings/SS-NOPE1").status_code == 404
