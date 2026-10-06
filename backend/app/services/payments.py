"""
Taking a deposit by M-Pesa.

Payment is asynchronous: the prompt is accepted immediately, and whether the
client entered their PIN arrives later on a callback. Nothing here trusts that
callback's numbers — it identifies the attempt, then settles against what we
recorded when we asked.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus, Payment, PaymentStatus
from app.services.mpesa import MpesaError, MpesaProvider, StkPushRequest

logger = logging.getLogger(__name__)

#: Safaricom uses 0 for success and its own codes for every way a payment did
#: not happen — cancelled, wrong PIN, insufficient funds, timed out.
SUCCESS_RESULT_CODE = 0


class PaymentError(Exception):
    """The deposit could not be requested."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def request_deposit(
    db: Session, booking: Booking, provider: MpesaProvider
) -> Payment:
    """
    Send the client a prompt for their deposit.

    The amount comes from the booking, which the server priced — never from
    anything a client sent.
    """
    try:
        result = provider.stk_push(
            StkPushRequest(
                phone=booking.customer_phone,
                amount_kes=booking.deposit_kes,
                account_reference=booking.reference,
                description=f"Deposit for {booking.reference}",
            )
        )
    except MpesaError as exc:
        logger.warning("STK push refused for %s: %s", booking.reference, exc)
        raise PaymentError(str(exc)) from exc

    payment = Payment(
        booking_id=booking.id,
        checkout_request_id=result.checkout_request_id,
        merchant_request_id=result.merchant_request_id,
        amount_kes=booking.deposit_kes,
        phone=booking.customer_phone,
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@dataclass(frozen=True)
class CallbackOutcome:
    """What a callback did, for logging and for the endpoint's reply."""

    handled: bool
    already_settled: bool
    detail: str


def _as_int(value: object) -> int | None:
    """Safaricom sends Amount as a number, but never assume it."""
    try:
        return int(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _extract(payload: dict[str, Any]) -> tuple[str, int, str, dict[str, Any]]:
    """
    Pull what matters out of Safaricom's envelope.

    The shape is Body.stkCallback, with the receipt buried in an item list that
    is only present on success.
    """
    callback = (payload.get("Body") or {}).get("stkCallback") or {}

    checkout_request_id = callback.get("CheckoutRequestID") or ""
    result_code = callback.get("ResultCode")
    result_desc = callback.get("ResultDesc") or ""

    items = {
        item.get("Name"): item.get("Value")
        for item in ((callback.get("CallbackMetadata") or {}).get("Item") or [])
        if isinstance(item, dict)
    }

    if not checkout_request_id or result_code is None:
        raise ValueError("Callback is missing CheckoutRequestID or ResultCode")

    return checkout_request_id, int(result_code), result_desc, items


def handle_callback(db: Session, payload: dict[str, Any]) -> CallbackOutcome:
    """
    Settle a payment from Safaricom's callback.

    Idempotent: Safaricom retries until it gets a 200, so the same confirmation
    arrives more than once and must settle the booking exactly once.
    """
    checkout_request_id, result_code, result_desc, items = _extract(payload)

    payment = db.scalar(
        select(Payment).where(Payment.checkout_request_id == checkout_request_id)
    )
    if payment is None:
        # Not ours. Report it handled so Safaricom stops retrying, but say so
        # loudly: it is either a forged post or a bug on our side.
        logger.warning("Callback for unknown checkout id %s", checkout_request_id)
        return CallbackOutcome(False, False, "Unknown payment")

    if payment.status is not PaymentStatus.PENDING:
        return CallbackOutcome(True, True, f"Already {payment.status.value}")

    payment.result_code = result_code
    payment.result_desc = result_desc
    payment.completed_at = _now()

    booking = payment.booking

    if result_code != SUCCESS_RESULT_CODE:
        payment.status = PaymentStatus.FAILED
        # The hold is left alone rather than expired: it lapses on its own, and
        # until it does the client can answer a fresh prompt without losing the
        # slot to someone else.
        db.commit()
        return CallbackOutcome(True, False, f"Payment failed: {result_desc}")

    # Safaricom sends the amount back as a number; compare against what we asked
    # for rather than believing the payload, so a forged or altered callback
    # cannot confirm a booking that was not paid for. An unparseable amount is
    # treated the same as a wrong one — letting the ValueError escape would be
    # swallowed by the endpoint's parse handler and strand the payment pending.
    paid = _as_int(items.get("Amount"))

    if paid is None or paid != payment.amount_kes:
        payment.status = PaymentStatus.FAILED
        payment.result_desc = (
            f"Amount mismatch: expected {payment.amount_kes}, callback said {paid}"
        )
        logger.error(
            "Amount mismatch on %s: expected %s, got %s",
            booking.reference,
            payment.amount_kes,
            paid,
        )
        db.commit()
        return CallbackOutcome(True, False, "Amount mismatch")

    payment.mpesa_receipt = str(items.get("MpesaReceiptNumber") or "") or None

    # The booking may no longer be claimable: a hold lapses after HOLD_MINUTES
    # and the slot is released, so by the time a late confirmation arrives
    # somebody else may hold it. Confirming regardless would violate the slot
    # index and crash in a retry loop, and silently dropping it would lose the
    # fact that the client's money moved.
    if booking.status is not BookingStatus.PENDING_PAYMENT:
        payment.status = PaymentStatus.ORPHANED
        payment.result_desc = (
            f"Paid after the booking became {booking.status.value}; "
            "needs a refund or a new slot."
        )
        logger.error(
            "ORPHANED PAYMENT on %s: receipt %s, KES %s, booking is %s",
            booking.reference,
            payment.mpesa_receipt,
            payment.amount_kes,
            booking.status.value,
        )
        db.commit()
        return CallbackOutcome(True, False, "Paid, but the slot was gone")

    payment.status = PaymentStatus.SUCCEEDED

    # The deposit cleared, so the slot is the client's; the hold has done its job.
    booking.status = BookingStatus.CONFIRMED
    booking.hold_expires_at = None

    db.commit()
    return CallbackOutcome(True, False, "Payment confirmed")
