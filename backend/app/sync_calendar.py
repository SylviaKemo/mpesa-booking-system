"""
Put any confirmed bookings the calendar is missing into it.

Every confirmation already triggers this sweep, so it only has work to do after
a Google outage — and only until the next booking, which retries anyway. Run it
to catch up without waiting, or from cron so a quiet day after an outage still
catches up:

    python -m app.sync_calendar

Safe to run any number of times: a booking already in the calendar is skipped.
"""

import logging

from app.database import SessionLocal
from app.services.calendar import get_calendar, sync_confirmed_bookings


def main() -> None:
    # The sweep logs each failure; without a handler they would be dropped.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    db = SessionLocal()
    try:
        synced = sync_confirmed_bookings(db, get_calendar())
        print(f"Added {synced} booking(s) to the calendar.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
