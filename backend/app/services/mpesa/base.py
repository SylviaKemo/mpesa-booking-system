"""
The shape of an M-Pesa provider.

Everything above this line works against the protocol, so the Daraja HTTP
client and the in-memory fake are interchangeable and the booking flow can be
exercised without credentials or a public callback URL.
"""

from dataclasses import dataclass
from typing import Protocol


class MpesaError(Exception):
    """The provider could not be reached, or refused the request."""


@dataclass(frozen=True)
class StkPushRequest:
    """A prompt to send to a handset."""

    #: 2547XXXXXXXX, as stored on the booking.
    phone: str
    #: Whole shillings. M-Pesa has no concept of cents here.
    amount_kes: int
    #: Shown on the client's statement; our booking reference.
    account_reference: str
    description: str


@dataclass(frozen=True)
class StkPushResult:
    """
    What Safaricom returns when a prompt is accepted.

    Acceptance only means the prompt was sent. Whether the client entered their
    PIN arrives later, on the callback.
    """

    checkout_request_id: str
    merchant_request_id: str
    customer_message: str


class MpesaProvider(Protocol):
    def stk_push(self, request: StkPushRequest) -> StkPushResult:
        """
        Send a payment prompt.

        Raises MpesaError if the request was rejected or the provider could not
        be reached; the caller decides what that means for the booking.
        """
        ...
