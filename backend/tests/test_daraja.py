"""
The Daraja client, exercised without touching Safaricom.

httpx2's MockTransport stands in for the network, so every branch — token
caching, refusal, malformed responses — is covered without credentials or a
public callback URL. What it cannot prove is that Safaricom accepts the request
we build; that needs one live sandbox call.
"""

import base64
from datetime import datetime, timedelta, timezone

import httpx2
import pytest

from app.config import Settings
from app.services.mpesa import DarajaProvider, MpesaError, StkPushRequest

TOKEN_PATH = "/oauth/v1/generate"
STK_PATH = "/mpesa/stkpush/v1/processrequest"


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "mpesa_provider": "daraja",
        "mpesa_consumer_key": "the-key",
        "mpesa_consumer_secret": "the-secret",
        "mpesa_shortcode": "174379",
        "mpesa_passkey": "the-passkey",
        "mpesa_callback_secret": "cb-secret",
        "mpesa_callback_base_url": "https://salon.test",
        "mpesa_api_base_url": "https://sandbox.safaricom.co.ke",
    }
    base.update(overrides)
    return Settings(**base)


def _request() -> StkPushRequest:
    return StkPushRequest(
        phone="254712345678",
        amount_kes=600,
        account_reference="SS-ABC12",
        description="Deposit for SS-ABC12",
    )


def _provider(handler, **setting_overrides: object) -> tuple[DarajaProvider, list]:
    """A provider wired to a scripted transport, plus the requests it made."""
    seen: list[httpx2.Request] = []

    def record(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return handler(request)

    settings = _settings(**setting_overrides)
    client = httpx2.Client(
        base_url=settings.mpesa_api_base_url, transport=httpx2.MockTransport(record)
    )
    return DarajaProvider(settings, client=client), seen


def _ok(request: httpx2.Request) -> httpx2.Response:
    if TOKEN_PATH in request.url.path:
        return httpx2.Response(
            200, json={"access_token": "tok-1", "expires_in": "3599"}
        )
    return httpx2.Response(
        200,
        json={
            "MerchantRequestID": "m-1",
            "CheckoutRequestID": "ws_CO_1",
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "CustomerMessage": "Success. Request accepted for processing",
        },
    )


def test_a_prompt_is_sent_and_its_identifiers_returned() -> None:
    provider, _ = _provider(_ok)

    result = provider.stk_push(_request())

    assert result.checkout_request_id == "ws_CO_1"
    assert result.merchant_request_id == "m-1"


def test_the_request_carries_what_daraja_requires() -> None:
    import json

    provider, seen = _provider(_ok)
    provider.stk_push(_request())

    stk = next(r for r in seen if STK_PATH in r.url.path)
    body = json.loads(stk.content)

    assert body["BusinessShortCode"] == "174379"
    assert body["PartyA"] == body["PhoneNumber"] == "254712345678"
    # Daraja rejects a decimal amount.
    assert body["Amount"] == 600 and isinstance(body["Amount"], int)
    assert body["AccountReference"] == "SS-ABC12"
    assert body["CallBackURL"] == "https://salon.test/api/mpesa/callback/cb-secret"
    assert stk.headers["Authorization"] == "Bearer tok-1"


def test_the_password_is_the_documented_base64_triple() -> None:
    """base64(shortcode + passkey + timestamp) — wrong and every push is refused."""
    import json

    provider, seen = _provider(_ok)
    provider.stk_push(_request())

    body = json.loads(next(r for r in seen if STK_PATH in r.url.path).content)
    expected = base64.b64encode(
        f"174379the-passkey{body['Timestamp']}".encode()
    ).decode()

    assert body["Password"] == expected


def test_the_timestamp_is_on_the_salon_clock() -> None:
    """
    Daraja validates the timestamp against East African time, so a UTC host
    would be three hours out and have every request rejected.
    """
    import json

    provider, seen = _provider(_ok)
    provider.stk_push(_request())

    body = json.loads(next(r for r in seen if STK_PATH in r.url.path).content)
    stamped = datetime.strptime(body["Timestamp"], "%Y%m%d%H%M%S")
    nairobi = datetime.now(_settings().tz).replace(tzinfo=None)

    assert abs((stamped - nairobi).total_seconds()) < 60


def test_the_token_is_fetched_once_and_reused() -> None:
    """It lasts about an hour; fetching one per booking would double every request."""
    provider, seen = _provider(_ok)

    provider.stk_push(_request())
    provider.stk_push(_request())

    assert sum(1 for r in seen if TOKEN_PATH in r.url.path) == 1
    assert sum(1 for r in seen if STK_PATH in r.url.path) == 2


def test_an_expired_token_is_refetched() -> None:
    provider, seen = _provider(_ok)
    provider.stk_push(_request())

    provider._token_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    provider.stk_push(_request())

    assert sum(1 for r in seen if TOKEN_PATH in r.url.path) == 2


def test_bad_credentials_are_reported_clearly() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(400, json={"errorMessage": "Bad Request"})

    provider, _ = _provider(handler)

    with pytest.raises(MpesaError, match="refused the credentials"):
        provider.stk_push(_request())


def test_a_token_outage_is_not_blamed_on_the_credentials() -> None:
    """
    Told it was a credentials problem, you would go and check perfectly good
    keys while Safaricom was simply down.
    """

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(503, json={})

    provider, _ = _provider(handler)

    with pytest.raises(MpesaError, match="could not issue a token"):
        provider.stk_push(_request())


def test_a_declining_response_code_is_not_treated_as_success() -> None:
    """
    Daraja answers 200 with a non-zero ResponseCode when the prompt was not
    sent; reading only the status would lose that silently.
    """

    def handler(request: httpx2.Request) -> httpx2.Response:
        if TOKEN_PATH in request.url.path:
            return httpx2.Response(200, json={"access_token": "t", "expires_in": "3599"})
        return httpx2.Response(
            200,
            json={"ResponseCode": "1", "ResponseDescription": "Invalid Amount"},
        )

    provider, _ = _provider(handler)

    with pytest.raises(MpesaError, match="Invalid Amount"):
        provider.stk_push(_request())


def test_a_rejected_push_surfaces_daraja_s_reason() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        if TOKEN_PATH in request.url.path:
            return httpx2.Response(200, json={"access_token": "t", "expires_in": "3599"})
        return httpx2.Response(
            400, json={"errorMessage": "Invalid PhoneNumber"}
        )

    provider, _ = _provider(handler)

    with pytest.raises(MpesaError, match="Invalid PhoneNumber"):
        provider.stk_push(_request())


def test_a_missing_checkout_id_is_an_error() -> None:
    """Without it no callback could ever be matched to this attempt."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        if TOKEN_PATH in request.url.path:
            return httpx2.Response(200, json={"access_token": "t", "expires_in": "3599"})
        return httpx2.Response(200, json={"ResponseCode": "0", "MerchantRequestID": "m"})

    provider, _ = _provider(handler)

    with pytest.raises(MpesaError, match="CheckoutRequestID"):
        provider.stk_push(_request())


def test_an_html_error_page_does_not_crash_the_parse() -> None:
    """Daraja answers with HTML when something is badly wrong."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        if TOKEN_PATH in request.url.path:
            return httpx2.Response(200, json={"access_token": "t", "expires_in": "3599"})
        return httpx2.Response(502, text="<html>Bad Gateway</html>")

    provider, _ = _provider(handler)

    with pytest.raises(MpesaError, match="non-JSON"):
        provider.stk_push(_request())


def test_an_unreachable_daraja_becomes_an_mpesa_error() -> None:
    """The caller treats MpesaError as 'hold the booking', so it must not leak httpx2."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("no route to host")

    provider, _ = _provider(handler)

    with pytest.raises(MpesaError, match="Could not reach Daraja"):
        provider.stk_push(_request())
