import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, EnumValue, UtcDateTime
from app.models.booking import Booking


class PaymentStatus(str, enum.Enum):
    #: Prompt accepted by Safaricom; the client has not answered it yet.
    PENDING = "pending"
    #: Callback confirmed the money moved.
    SUCCEEDED = "succeeded"
    #: Cancelled, wrong PIN, insufficient funds, or timed out.
    FAILED = "failed"
    #: The money moved, but the slot was gone by the time we heard. Needs a
    #: person: the client has paid for a booking they do not have.
    ORPHANED = "orphaned"


class Payment(Base):
    """
    One M-Pesa deposit attempt.

    A row per attempt rather than a column on the booking, because a client may
    cancel a prompt and try again, and the failures matter when someone phones
    to ask why their money left but the slot did not stick.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    booking_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Safaricom's handle for the prompt, and our idempotency key: callbacks are
    # retried, so the same confirmation can arrive several times and must settle
    # the booking exactly once.
    checkout_request_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    merchant_request_id: Mapped[str] = mapped_column(String(64), nullable=False)

    #: What we asked for, kept to check the callback against.
    amount_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=False)

    status: Mapped[PaymentStatus] = mapped_column(
        EnumValue(PaymentStatus, 12), nullable=False, default=PaymentStatus.PENDING
    )

    #: Safaricom's verdict. 0 means paid; everything else is a reason it did not.
    result_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: The receipt the client sees in their SMS, e.g. "SGH3RTY89K".
    mpesa_receipt: Mapped[str | None] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)

    booking: Mapped[Booking] = relationship(back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount_kes > 0", name="ck_payments_amount_positive"),
    )
