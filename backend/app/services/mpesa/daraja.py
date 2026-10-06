"""
The real M-Pesa client, talking to Safaricom's Daraja API.

Two calls are involved. Authorization exchanges the consumer key and secret for
a short-lived bearer token, and STK push uses that token to send the prompt.
The token is cached because it lasts about an hour and fetching one per booking
would double every request for nothing.
"""

import base64
import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx2

from app.config import Settings
from app.services.mpesa.base import MpesaError, StkPushRequest, StkPushResult

logger = logging.getLogger(__name__)

_TOKEN_PATH = "/oauth/v1/generate?grant_type=client_credentials"
_STK_PATH = "/mpesa/stkpush/v1/processrequest"

#: Safaricom times the token out after an hour. Refreshing a little early
#: avoids racing the expiry on a request already in flight.
_TOKEN_SAFETY_MARGIN = timedelta(seconds=60)

#: A paybill. A till number would be CustomerBuyGoodsOnline.
_TRANSACTION_TYPE = "CustomerPayBillOnline"

_TIMEOUT_SECONDS = 30


class DarajaProvider:
    """
    Sends real prompts. Satisfies the same protocol as the fake, so nothing
    above this line changes when it is swapped in.
    """

    def __init__(
        self, settings: Settings, client: httpx2.Client | None = None
    ) -> None:
        self._settings = settings
        self._client = client or httpx2.Client(
            base_url=settings.mpesa_api_base_url, timeout=_TIMEOUT_SECONDS
        )
        # FastAPI serves sync endpoints from a threadpool, so two bookings can
        # reach the token check at once and would otherwise both fetch one.
        self._lock = threading.Lock()
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    # ---------------------------------------------------------------- tokens

    def _token_is_live(self) -> bool:
        return (
            self._token is not None
            and self._token_expires_at is not None
            and datetime.now(timezone.utc) < self._token_expires_at
        )

    def _access_token(self) -> str:
        with self._lock:
            if self._token_is_live():
                return self._token  # type: ignore[return-value]

            try:
                response = self._client.get(
                    _TOKEN_PATH,
                    auth=httpx2.BasicAuth(
                        self._settings.mpesa_consumer_key,
                        self._settings.mpesa_consumer_secret,
                    ),
                )
            except httpx2.HTTPError as exc:
                raise MpesaError(f"Could not reach Daraja for a token: {exc}") from exc

            if response.status_code in (400, 401, 403):
                # The key and secret are wrong, or the app is not activated —
                # retrying will not help and the fix is a config change.
                raise MpesaError(
                    f"Daraja refused the credentials ({response.status_code})"
                )
            if response.status_code != 200:
                # An outage on their side, not something we sent. Worth saying
                # so: told it was a credentials problem, you would go and check
                # perfectly good keys.
                raise MpesaError(
                    f"Daraja could not issue a token ({response.status_code})"
                )

            payload = _json(response)
            token = payload.get("access_token")
            if not token:
                raise MpesaError("Daraja returned no access token")

            # expires_in is seconds, and arrives as a string.
            expires_in = int(payload.get("expires_in") or 3599)
            self._token = str(token)
            self._token_expires_at = (
                datetime.now(timezone.utc)
                + timedelta(seconds=expires_in)
                - _TOKEN_SAFETY_MARGIN
            )
            return self._token

    # ------------------------------------------------------------- stk push

    def _password(self, timestamp: str) -> str:
        """
        base64(shortcode + passkey + timestamp), as Daraja specifies.

        Not a secret in itself — it is derived per request and only valid with
        the matching timestamp — but the passkey inside it is.
        """
        raw = f"{self._settings.mpesa_shortcode}{self._settings.mpesa_passkey}{timestamp}"
        return base64.b64encode(raw.encode()).decode()

    def _timestamp(self) -> str:
        """
        YYYYMMDDHHMMSS on the salon's clock.

        Daraja validates this against East African time, so a UTC host would be
        three hours out and have its requests rejected.
        """
        return datetime.now(self._settings.tz).strftime("%Y%m%d%H%M%S")

    def stk_push(self, request: StkPushRequest) -> StkPushResult:
        timestamp = self._timestamp()

        body: dict[str, Any] = {
            "BusinessShortCode": self._settings.mpesa_shortcode,
            "Password": self._password(timestamp),
            "Timestamp": timestamp,
            "TransactionType": _TRANSACTION_TYPE,
            # Daraja rejects a decimal here; deposits are whole shillings anyway.
            "Amount": int(request.amount_kes),
            "PartyA": request.phone,
            "PartyB": self._settings.mpesa_shortcode,
            "PhoneNumber": request.phone,
            "CallBackURL": self._settings.mpesa_callback_url,
            "AccountReference": request.account_reference,
            "TransactionDesc": request.description,
        }

        try:
            response = self._client.post(
                _STK_PATH,
                json=body,
                headers={"Authorization": f"Bearer {self._access_token()}"},
            )
        except httpx2.HTTPError as exc:
            raise MpesaError(f"Could not reach Daraja: {exc}") from exc

        payload = _json(response)

        if response.status_code != 200:
            # Daraja puts the reason in errorMessage on a rejection.
            reason = payload.get("errorMessage") or f"HTTP {response.status_code}"
            raise MpesaError(f"Daraja rejected the request: {reason}")

        # A 200 still carries a code: anything but "0" means the prompt was not
        # sent, so treating 200 as success would lose the failure silently.
        if str(payload.get("ResponseCode")) != "0":
            raise MpesaError(
                f"Daraja declined the prompt: "
                f"{payload.get('ResponseDescription') or payload.get('ResponseCode')}"
            )

        checkout_request_id = payload.get("CheckoutRequestID")
        if not checkout_request_id:
            # Without it we could never match the callback to this attempt.
            raise MpesaError("Daraja returned no CheckoutRequestID")

        return StkPushResult(
            checkout_request_id=str(checkout_request_id),
            merchant_request_id=str(payload.get("MerchantRequestID") or ""),
            customer_message=str(payload.get("CustomerMessage") or ""),
        )


def _json(response: httpx2.Response) -> dict[str, Any]:
    """Daraja answers with HTML when something is badly wrong, so guard the parse."""
    try:
        payload = response.json()
    except ValueError as exc:
        raise MpesaError(
            f"Daraja returned a non-JSON response ({response.status_code})"
        ) from exc

    return payload if isinstance(payload, dict) else {}
