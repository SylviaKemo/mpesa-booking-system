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


@pytest.mark.usefixtures("seeded")
def test_a_payment_that_lands_after_the_slot_is_gone_is_flagged_not_dropped(
    client: TestClient, db: Session
) -> None:
    """
    The money moved but the slot did not survive. Confirming anyway violates
    the slot index and the IntegrityError escapes as a 500, which Safaricom
    retries forever; dropping it loses the fact that someone paid.
    """
    from datetime import timedelta

    from app.models import PaymentMethod
    from app.services.booking import expire_stale_holds

    created = client.post("/api/bookings", json=_payload()).json()
    payment = db.query(Payment).one()

    # The hold lapses and the slot is released.
    booking = db.query(Booking).one()
    booking.hold_expires_at = booking.hold_expires_at - timedelta(hours=1)
    db.commit()
    expire_stale_holds(db)
    db.commit()

    # Someone else takes the freed slot.
    taken = client.post(
        "/api/bookings", json=_payload(name="Next Client", payment_method="studio")
    )
    assert taken.status_code == 201

    # The original payment confirms late.
    response = _post_callback(
        client, _callback(payment.checkout_request_id, amount=created["deposit_kes"])
    )

    assert response.status_code == 200, "a 500 here would retry forever"

    db.expire_all()
    settled = db.query(Payment).one()
    assert settled.status is PaymentStatus.ORPHANED
    # The receipt is what a refund will be traced by.
    assert settled.mpesa_receipt == "SGH3RTY89K"
    assert "refund" in (settled.result_desc or "")

    original = db.query(Booking).filter_by(reference=created["reference"]).one()
    assert original.status is BookingStatus.EXPIRED
    # Exactly one live booking on that slot: the one that actually holds it.
    assert db.query(Booking).filter_by(status=BookingStatus.CONFIRMED).count() == 1


@pytest.mark.usefixtures("seeded")
def test_the_lookup_reveals_no_personal_data(client: TestClient) -> None:
    """
    A reference is five characters and the endpoint is unauthenticated, so it is
    enumerable. A guess must not buy a name, a mobile number, or a note that may
    be medical.
    """
    created = client.post(
        "/api/bookings", json=_payload(name="Grace Mwangi", notes="sensitive eyes")
    ).json()

    body = client.get(f"/api/bookings/{created['reference']}").json()

    for leaked in ("customer_name", "customer_phone", "notes"):
        assert leaked not in body, f"{leaked} is readable by anyone with a reference"

    # Still answers what the polling exists for.
    assert body["status"] == BookingStatus.PENDING_PAYMENT.value
    assert body["deposit_kes"] == created["deposit_kes"]
    assert body["payments"][0]["status"] == PaymentStatus.PENDING.value


@pytest.mark.usefixtures("seeded")
def test_a_provider_outage_still_tells_the_client_their_reference(
    client: TestClient, mpesa: FakeMpesaProvider
) -> None:
    """
    Without it they hold a slot they cannot poll for, and retrying collides with
    their own booking.
    """
    mpesa.fail_with = MpesaError("Daraja unavailable")

    response = client.post("/api/bookings", json=_payload())

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["reference"].startswith("SS-")
    # And that reference resolves, so they can poll or be helped over the phone.
    assert client.get(f"/api/bookings/{detail['reference']}").status_code == 200


@pytest.mark.usefixtures("seeded")
def test_an_unparseable_amount_fails_the_payment_rather_than_stranding_it(
    client: TestClient, db: Session
) -> None:
    """
    Letting ValueError escape put this through a handler meant for malformed
    envelopes, which answered 200 and left the payment pending forever — no
    retry would ever come.
    """
    client.post("/api/bookings", json=_payload())
    payment = db.query(Payment).one()

    body = _callback(payment.checkout_request_id, amount=0)
    body["Body"]["stkCallback"]["CallbackMetadata"]["Item"][0]["Value"] = "not-a-number"

    response = _post_callback(client, body)

    assert response.status_code == 200
    db.expire_all()
    assert db.query(Payment).one().status is PaymentStatus.FAILED
    assert db.query(Booking).one().status is BookingStatus.PENDING_PAYMENT
