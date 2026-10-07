"""
An in-memory calendar.

Stands in until a Google service account and a shared calendar exist. It
records what it was asked to add so tests can assert on it, and can be told to
fail so the unhappy path is exercised too.

Selected whenever CALENDAR_PROVIDER is "fake". Production refuses that — see
Settings._calendar_configured.
"""

from dataclasses import dataclass, field

from app.services.calendar.base import CalendarError, CalendarEvent


@dataclass
class FakeCalendarProvider:
    """Records events instead of sending them."""

    events: list[CalendarEvent] = field(default_factory=list)
    #: Set to raise from every add_event, standing in for an outage.
    fail_with: CalendarError | None = None

    def add_event(self, event: CalendarEvent) -> None:
        if self.fail_with is not None:
            raise self.fail_with

        # Google answers a repeated event id with a conflict, which the real
        # client treats as success. Mirror that, so a test of a retried sync
        # sees one event rather than two.
        if any(existing.event_id == event.event_id for existing in self.events):
            return
        self.events.append(event)

    def reset(self) -> None:
        self.events.clear()
        self.fail_with = None


#: A single instance, so a test can inspect what a request added.
fake_calendar = FakeCalendarProvider()
