from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import PaymentMethod


class SlotOut(BaseModel):
    # Built from the SlotAvailability dataclass the service returns.
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str
    available: bool


class AvailabilityOut(BaseModel):
    date: date
    slots: list[SlotOut]


class BookingCreate(BaseModel):
    """
    What a client may send.

    Deliberately carries no amount: the server prices the booking from the ids
    below, so a tampered total changes nothing.
    """

    tier_id: str = Field(min_length=1, max_length=32)
    addition_ids: list[str] = Field(default_factory=list, max_length=20)
    booking_date: date
    slot_key: str = Field(min_length=1, max_length=8)

    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=20)
    notes: str | None = Field(default=None, max_length=1000)
    payment_method: PaymentMethod


class BookingAdditionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    addition_id: str
    amount_kes: int
    minutes: int


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    amount_kes: int
    #: Null until the callback arrives; present once the money moved.
    mpesa_receipt: str | None
    result_desc: str | None


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference: str
    booking_date: date
    slot_key: str
    status: str
    payment_method: str

    tier_id: str
    additions: list[BookingAdditionOut]

    amount_kes: int
    deposit_kes: int
    minutes: int

    customer_name: str
    customer_phone: str
    notes: str | None

    hold_expires_at: datetime | None

    #: The deposit attempts, oldest first. Empty for a studio booking.
    payments: list[PaymentOut] = []
