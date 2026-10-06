"""
Importing every model here registers it on Base.metadata, which is what
Alembic autogenerate compares the database against.
"""

from app.models.booking import (
    BLOCKING_STATUSES,
    LIVE_BOOKING_PREDICATE,
    Booking,
    BookingAddition,
    BookingStatus,
    PaymentMethod,
)
from app.models.catalogue import Addition, LashSet, Tier

__all__ = [
    "Addition",
    "BLOCKING_STATUSES",
    "Booking",
    "BookingAddition",
    "BookingStatus",
    "LIVE_BOOKING_PREDICATE",
    "LashSet",
    "PaymentMethod",
    "Tier",
]
