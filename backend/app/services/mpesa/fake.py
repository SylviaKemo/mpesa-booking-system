"""
An in-memory M-Pesa provider.

Stands in until Daraja credentials and a public callback URL exist. It records
what it was asked to send so tests can assert on it, and can be told to fail so
the unhappy path is exercised too.

Selected whenever MPESA_PROVIDER is "fake". Production refuses that — see
Settings._real_provider_in_production.
"""

import itertools
from dataclasses import dataclass, field

from app.services.mpesa.base import (
    MpesaError,
    StkPushRequest,
    StkPushResult,
)


@dataclass
class FakeMpesaProvider:
    """Records prompts instead of sending them."""

    sent: list[StkPushRequest] = field(default_factory=list)
    #: Set to raise from the next stk_push, standing in for a refusal or outage.
    fail_with: MpesaError | None = None

    _counter: itertools.count = field(default_factory=lambda: itertools.count(1))

    def stk_push(self, request: StkPushRequest) -> StkPushResult:
        if self.fail_with is not None:
            raise self.fail_with

        self.sent.append(request)
        n = next(self._counter)
        return StkPushResult(
            checkout_request_id=f"ws_CO_fake_{n}",
            merchant_request_id=f"fake-merchant-{n}",
            customer_message="Success. Request accepted for processing",
        )

    def reset(self) -> None:
        self.sent.clear()
        self.fail_with = None


#: A single instance, so a test can inspect what a request sent.
fake_provider = FakeMpesaProvider()
