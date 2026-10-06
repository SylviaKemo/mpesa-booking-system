from pydantic import BaseModel, ConfigDict


class TierOut(BaseModel):
    """A bookable volume. `amount_kes` names its currency so no caller guesses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    amount_kes: int
    minutes: int
    note: str | None = None


class LashSetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    blurb: str
    image_url: str
    image_alt: str
    tiers: list[TierOut]


class AdditionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    amount_kes: int
    minutes: int


class AdditionsCardOut(BaseModel):
    """
    Presentation copy for the additions card, not priced catalogue data.

    Frozen because a single instance is shared across every response; without
    it, mutating one response would change what every later request serves.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    blurb: str
    image_url: str
    image_alt: str


class CatalogueOut(BaseModel):
    sets: list[LashSetOut]
    additions: list[AdditionOut]
    additions_card: AdditionsCardOut
