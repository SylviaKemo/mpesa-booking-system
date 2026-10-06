"""
The salon's bookable start times.

A constant rather than a table: the times are fixed opening hours, not priced
catalogue data, and nothing in the product edits them yet. The key — not the
label — is what a booking stores and what the uniqueness constraint uses, so
rewording a label can never free or collide a slot.
"""

from datetime import date, datetime, time, tzinfo
from typing import Final, NamedTuple


class Slot(NamedTuple):
    key: str
    label: str
    start: time


SLOTS: Final[tuple[Slot, ...]] = (
    Slot("0900", "9:00 am", time(9, 0)),
    Slot("1000", "10:00 am", time(10, 0)),
    Slot("1130", "11:30 am", time(11, 30)),
    Slot("1300", "1:00 pm", time(13, 0)),
    Slot("1430", "2:30 pm", time(14, 30)),
    Slot("1600", "4:00 pm", time(16, 0)),
    Slot("1700", "5:00 pm", time(17, 0)),
    Slot("1800", "6:00 pm", time(18, 0)),
)

SLOTS_BY_KEY: Final[dict[str, Slot]] = {slot.key: slot for slot in SLOTS}


def get_slot(key: str) -> Slot | None:
    return SLOTS_BY_KEY.get(key)


def starts_at(slot: Slot, on: date, tz: tzinfo) -> datetime:
    """
    The instant a slot begins, in the salon's timezone.

    Slot times are the salon's wall clock, so they only become a point in time
    once anchored to a day and that timezone.
    """
    return datetime.combine(on, slot.start, tzinfo=tz)
