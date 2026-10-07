"""
The shape of a calendar provider.

Everything above this line works against the protocol, so the Google client and
the in-memory fake are interchangeable and bookings can be confirmed without a
Google project or a shared calendar.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class CalendarError(Exception):
    """The provider could not be reached, or refused the event."""


@dataclass(frozen=True)
class CalendarEvent:
    """One confirmed booking, as it appears in Shamim's calendar."""

    #: Derived from the booking reference, so adding the same booking twice
    #: names the same event instead of creating a second one.
    event_id: str
    summary: str
    description: str
    #: Timezone-aware, on the salon's clock.
    start: datetime
    end: datetime
    #: An IANA name, e.g. "Africa/Nairobi". Sent alongside the times so the
    #: event reads correctly on a phone set to any other zone.
    timezone: str


class CalendarProvider(Protocol):
    def add_event(self, event: CalendarEvent) -> None:
        """
        Put the event in the calendar.

        Adding an event that is already there succeeds without a duplicate:
        a sync retried after a lost response must not book Shamim twice.
        """
        ...
