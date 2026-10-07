"""Picks the calendar the app runs with."""

from functools import lru_cache

from app.config import get_settings
from app.services.calendar.base import CalendarProvider
from app.services.calendar.fake import fake_calendar
from app.services.calendar.google import GoogleCalendarProvider


@lru_cache
def _google() -> GoogleCalendarProvider:
    """Built once: it caches an access token, which a fresh instance would lose."""
    return GoogleCalendarProvider(get_settings())


def get_calendar() -> CalendarProvider:
    """
    The calendar for the current configuration.

    Production cannot select the fake — Settings refuses to start on it — so
    this choice is only ever real in a deployment.
    """
    if get_settings().calendar_provider == "google":
        return _google()
    return fake_calendar
