"""
The Google Calendar client, exercised without touching Google.

httpx2's MockTransport stands in for the network, and a key generated here
stands in for the service account, so the signed assertion is checked for real
without credentials. What this cannot prove is that Google accepts the event
we build; that needs one call against a real shared calendar.
"""

import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

import httpx2
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import Settings
from app.services.calendar import CalendarError, CalendarEvent, GoogleCalendarProvider

TOKEN_URL = "https://oauth2.googleapis.com/token"
CLIENT_EMAIL = "booking@shamim.iam.gserviceaccount.com"

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PRIVATE_PEM = _KEY.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "calendar_provider": "google",
        "google_calendar_id": "shamim@gmail.com",
        "google_service_account_json": json.dumps(
            {"client_email": CLIENT_EMAIL, "private_key": _PRIVATE_PEM}
        ),
    }
    base.update(overrides)
    return Settings(**base)


def _event() -> CalendarEvent:
    start = datetime(2026, 10, 10, 14, 30, tzinfo=ZoneInfo("Africa/Nairobi"))
    return CalendarEvent(
        event_id="abc123",
        summary="Grace Mwangi · Wispy set, Mid volume",
        description="Booking SS-ABC12",
        start=start,
        end=start + timedelta(minutes=150),
        timezone="Africa/Nairobi",
    )


def _provider(handler, **overrides: object) -> tuple[GoogleCalendarProvider, list]:
    """A provider wired to a scripted transport, plus the requests it made."""
    seen: list[httpx2.Request] = []

    def record(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return handler(request)

    client = httpx2.Client(transport=httpx2.MockTransport(record))
    return GoogleCalendarProvider(_settings(**overrides), client=client), seen


def _token(status: int = 200, **body: object) -> httpx2.Response:
    return httpx2.Response(
        status, json=body or {"access_token": "tok-1", "expires_in": 3599}
    )


def _answer(event_status: int, event_body: dict | None = None):
    """A handler that issues a token, then answers the insert with event_status."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        if str(request.url) == TOKEN_URL:
            return _token()
        return httpx2.Response(event_status, json=event_body or {"id": "abc123"})

    return handler


def test_the_event_is_inserted_into_the_shared_calendar() -> None:
    provider, seen = _provider(_answer(200))

    provider.add_event(_event())

    insert = seen[-1]
    assert insert.method == "POST"
    # The calendar id is an email address, so its @ must be escaped in the path.
    assert str(insert.url) == (
        "https://www.googleapis.com/calendar/v3/calendars/shamim%40gmail.com/events"
    )
    assert insert.headers["Authorization"] == "Bearer tok-1"

    body = json.loads(insert.content)
    assert body["id"] == "abc123"
    assert body["summary"] == "Grace Mwangi · Wispy set, Mid volume"
    # Nairobi wall-clock time with its offset, plus the zone so a phone set to
    # another one still shows the appointment at the right moment.
    assert body["start"] == {
        "dateTime": "2026-10-10T14:30:00+03:00",
        "timeZone": "Africa/Nairobi",
    }
    assert body["end"]["dateTime"] == "2026-10-10T17:00:00+03:00"


def test_the_token_request_is_a_signed_service_account_assertion() -> None:
    provider, seen = _provider(_answer(200))

    provider.add_event(_event())

    token_request = seen[0]
    form = parse_qs(token_request.content.decode())
    assert form["grant_type"] == ["urn:ietf:params:oauth:grant-type:jwt-bearer"]

    claims = jwt.decode(
        form["assertion"][0],
        _KEY.public_key(),
        algorithms=["RS256"],
        audience=TOKEN_URL,
    )
    assert claims["iss"] == CLIENT_EMAIL
    # Events only: enough to add a booking, not to read the rest of her calendar.
    assert claims["scope"] == "https://www.googleapis.com/auth/calendar.events"
    assert claims["exp"] - claims["iat"] <= 3600


def test_the_token_is_reused_across_events() -> None:
    provider, seen = _provider(_answer(200))

    provider.add_event(_event())
    provider.add_event(_event())

    assert [str(r.url) for r in seen].count(TOKEN_URL) == 1


def test_an_event_already_in_the_calendar_counts_as_added() -> None:
    """A retried insert whose first answer was lost must not fail the sync."""
    provider, _ = _provider(
        _answer(409, {"error": {"code": 409, "message": "The requested identifier already exists."}})
    )

    provider.add_event(_event())  # does not raise


def test_an_unshared_calendar_says_how_to_fix_it() -> None:
    provider, _ = _provider(
        _answer(404, {"error": {"code": 404, "message": "Not Found"}})
    )

    with pytest.raises(CalendarError, match=f"shared with {CLIENT_EMAIL}"):
        provider.add_event(_event())


def test_a_refused_key_is_reported() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return _token(400, error="invalid_grant", error_description="Invalid JWT Signature.")

    provider, _ = _provider(handler)

    with pytest.raises(CalendarError, match="Invalid JWT Signature"):
        provider.add_event(_event())


def test_a_google_outage_is_reported() -> None:
    provider, _ = _provider(_answer(503, {"error": {"code": 503, "message": "Backend Error"}}))

    with pytest.raises(CalendarError, match="503"):
        provider.add_event(_event())


def test_an_unreachable_google_is_reported() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("no route to host")

    provider, _ = _provider(handler)

    with pytest.raises(CalendarError, match="Could not reach Google"):
        provider.add_event(_event())


def test_a_revoked_token_is_dropped_so_the_next_attempt_fetches_another() -> None:
    answers = iter([401, 200])

    def handler(request: httpx2.Request) -> httpx2.Response:
        if str(request.url) == TOKEN_URL:
            return _token()
        return httpx2.Response(next(answers), json={})

    provider, seen = _provider(handler)

    with pytest.raises(CalendarError):
        provider.add_event(_event())
    provider.add_event(_event())

    assert [str(r.url) for r in seen].count(TOKEN_URL) == 2


def test_a_mangled_private_key_is_reported_not_raised_raw() -> None:
    """Losing the \\n escapes when pasting the key is the usual way this breaks."""
    provider, _ = _provider(
        _answer(200),
        google_service_account_json=json.dumps(
            {"client_email": CLIENT_EMAIL, "private_key": "-----BEGIN PRIVATE KEY----- nope"}
        ),
    )

    with pytest.raises(CalendarError, match="service account key"):
        provider.add_event(_event())
