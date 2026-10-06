"""
Importing every model here registers it on Base.metadata, which is what
Alembic autogenerate compares the database against.
"""

from app.models.booking import (
    BLOCKING_STATUSES,
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
    "LashSet",
    "PaymentMethod",
    "Tier",
]
