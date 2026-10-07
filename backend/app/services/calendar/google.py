"""
The real calendar client, talking to the Google Calendar API.

Two calls are involved. A service account signs a short JWT and exchanges it for
a bearer token, and inserting an event uses that token. The token is cached
because it lasts an hour and fetching one per booking would double every
request for nothing.

A service account rather than Shamim's own login: nobody has to sign in, and
the account can only touch the one calendar she shared with it.
"""

import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

import httpx2
import jwt

from app.config import Settings
from app.services.calendar.base import CalendarError, CalendarEvent

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

#: Events only — enough to add a booking, not to read or delete the rest of
#: her calendar.
_SCOPE = "https://www.googleapis.com/auth/calendar.events"

#: Google caps an assertion's lifetime at an hour.
_ASSERTION_LIFETIME = timedelta(hours=1)

#: Refreshing a little early avoids racing the expiry on a request in flight.
_TOKEN_SAFETY_MARGIN = timedelta(seconds=60)

_TIMEOUT_SECONDS = 30


class GoogleCalendarProvider:
    """
    Adds real events. Satisfies the same protocol as the fake, so nothing
    above this line changes when it is swapped in.
    """

    def __init__(
        self, settings: Settings, client: httpx2.Client | None = None
    ) -> None:
        # Settings has already checked this parses and has both fields.
        key = json.loads(settings.google_service_account_json)
        self._client_email: str = key["client_email"]
        self._private_key: str = key["private_key"]
        self._calendar_id = settings.google_calendar_id
        self._client = client or httpx2.Client(timeout=_TIMEOUT_SECONDS)
        # FastAPI runs background tasks from a threadpool, so two confirmations
        # can reach the token check at once and would otherwise both fetch one.
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

    def _assertion(self) -> str:
        """The signed JWT Google trades for a token, per its service account flow."""
        now = datetime.now(timezone.utc)
        claims = {
            "iss": self._client_email,
            "scope": _SCOPE,
            "aud": _TOKEN_URL,
            "iat": int(now.timestamp()),
            "exp": int((now + _ASSERTION_LIFETIME).timestamp()),
        }
        try:
            return jwt.encode(claims, self._private_key, algorithm="RS256")
        except (jwt.PyJWTError, ValueError, TypeError) as exc:
            # A mangled private_key — usually its \n escapes lost in copying.
            raise CalendarError(f"Could not sign with the service account key: {exc}") from exc

    def _access_token(self) -> str:
        with self._lock:
            if self._token_is_live():
                return self._token  # type: ignore[return-value]

            try:
                response = self._client.post(
                    _TOKEN_URL,
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                        "assertion": self._assertion(),
                    },
                )
            except httpx2.HTTPError as exc:
                raise CalendarError(f"Could not reach Google for a token: {exc}") from exc

            payload = _json(response)

            if response.status_code in (400, 401, 403):
                # A revoked or deleted key, or a clock badly out — retrying
                # will not help and the fix is a config change.
                raise CalendarError(
                    f"Google refused the service account ({response.status_code}): "
                    f"{payload.get('error_description') or payload.get('error') or ''}"
                )
            if response.status_code != 200:
                raise CalendarError(
                    f"Google could not issue a token ({response.status_code})"
                )

            token = payload.get("access_token")
            if not token:
                raise CalendarError("Google returned no access token")

            expires_in = int(payload.get("expires_in") or 3599)
            self._token = str(token)
            self._token_expires_at = (
                datetime.now(timezone.utc)
                + timedelta(seconds=expires_in)
                - _TOKEN_SAFETY_MARGIN
            )
            return self._token

    def _forget_token(self) -> None:
        with self._lock:
            self._token = None
            self._token_expires_at = None

    # ---------------------------------------------------------------- events

    def add_event(self, event: CalendarEvent) -> None:
        body: dict[str, Any] = {
            # Our id rather than Google's, so a retried insert is refused as a
            # duplicate instead of creating a second event.
            "id": event.event_id,
            "summary": event.summary,
            "description": event.description,
            "start": {"dateTime": event.start.isoformat(), "timeZone": event.timezone},
            "end": {"dateTime": event.end.isoformat(), "timeZone": event.timezone},
        }
        url = _EVENTS_URL.format(calendar_id=quote(self._calendar_id, safe=""))

        try:
            response = self._client.post(
                url,
                json=body,
                headers={"Authorization": f"Bearer {self._access_token()}"},
            )
        except httpx2.HTTPError as exc:
            raise CalendarError(f"Could not reach Google Calendar: {exc}") from exc

        if response.status_code in (200, 201):
            return

        if response.status_code == 409:
            # The id is taken: an earlier attempt landed but its answer was
            # lost. The event is there, which is all that was asked.
            return

        if response.status_code == 401:
            # Revoked between calls. Drop it so the next attempt fetches fresh.
            self._forget_token()

        reason = _error_message(response)
        if response.status_code in (403, 404):
            # The usual cause by far: the calendar was never shared with the
            # service account, or the id names a different calendar.
            raise CalendarError(
                f"Google Calendar refused access ({response.status_code}): {reason}. "
                f"Check the calendar is shared with {self._client_email} "
                "with permission to make changes to events."
            )
        raise CalendarError(
            f"Google Calendar rejected the event ({response.status_code}): {reason}"
        )


def _json(response: httpx2.Response) -> dict[str, Any]:
    """An error page from a proxy is HTML, so guard the parse."""
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _error_message(response: httpx2.Response) -> str:
    """Google puts the reason in error.message."""
    error = _json(response).get("error")
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])
    return f"HTTP {response.status_code}"
