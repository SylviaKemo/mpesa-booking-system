import enum
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UtcDateTime
from app.models.catalogue import Addition, Tier


class BookingStatus(str, enum.Enum):
    """
    M-Pesa confirms asynchronously, so a booking is a small state machine
    rather than a single row that either exists or does not.
    """

    # Deposit by M-Pesa: the slot is held while the payment is confirmed.
    PENDING_PAYMENT = "pending_payment"
    # Paying at the studio, or a deposit that cleared.
    CONFIRMED = "confirmed"
    # A held slot whose payment never arrived; the slot is free again.
    EXPIRED = "expired"
    CANCELLED = "cancelled"


#: Statuses that occupy a slot. Anything else leaves it bookable.
BLOCKING_STATUSES: tuple[BookingStatus, ...] = (
    BookingStatus.PENDING_PAYMENT,
    BookingStatus.CONFIRMED,
)


class PaymentMethod(str, enum.Enum):
    MPESA = "mpesa"
    STUDIO = "studio"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    #: Shown to the client, e.g. "SS-4KD9P". Unique so it can identify a booking.
    reference: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)

    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    #: The slot's stable key, not its label — see app/slots.py.
    slot_key: Mapped[str] = mapped_column(String(8), nullable=False)

    status: Mapped[BookingStatus] = mapped_column(String(20), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(String(10), nullable=False)

    tier_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("tiers.id"), nullable=False
    )

    # Priced by the server at booking time and frozen here. A later catalogue
    # change must not silently alter what someone already agreed to pay.
    amount_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    deposit_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    #: Normalised to 2547XXXXXXXX so M-Pesa and reminders have one format.
    customer_phone: Mapped[str] = mapped_column(String(15), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    #: When an unpaid hold lapses. Null once the booking is settled.
    hold_expires_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, nullable=False, server_default=func.now()
    )

    tier: Mapped[Tier] = relationship()
    additions: Mapped[list["BookingAddition"]] = relationship(
        back_populates="booking", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("amount_kes >= 0", name="ck_bookings_amount_non_negative"),
        CheckConstraint("deposit_kes >= 0", name="ck_bookings_deposit_non_negative"),
        CheckConstraint("minutes > 0", name="ck_bookings_minutes_positive"),
        # One live booking per slot. Partial, so a cancelled or expired booking
        # frees the slot instead of blocking it forever. Supported by both
        # SQLite and Postgres.
        Index(
            "uq_bookings_live_slot",
            "booking_date",
            "slot_key",
            unique=True,
            sqlite_where=text(
                "status IN ('pending_payment', 'confirmed')"
            ),
            postgresql_where=text(
                "status IN ('pending_payment', 'confirmed')"
            ),
        ),
    )


class BookingAddition(Base):
    """
    The additions on a booking, with the price charged at the time.

    A link row rather than a list on the booking, so each addition keeps its own
    frozen amount and a later price change cannot rewrite history.
    """

    __tablename__ = "booking_additions"

    booking_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bookings.id", ondelete="CASCADE"), primary_key=True
    )
    addition_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("additions.id"), primary_key=True
    )
    amount_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="additions")
    addition: Mapped[Addition] = relationship()
