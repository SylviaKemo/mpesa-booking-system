from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Identifiers are the slugs the frontend already uses ("wispy", "wispy-mid"),
# not surrogate integers: they are stable, readable in a booking record, and
# let the client keep sending the ids it has always sent.
_ID = String(32)


class LashSet(Base):
    """A family of lash sets, e.g. "Wispy set", holding one or more tiers."""

    __tablename__ = "lash_sets"

    id: Mapped[str] = mapped_column(_ID, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    blurb: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    image_alt: Mapped[str] = mapped_column(String(160), nullable=False)

    # Display order is editorial, not alphabetical, and row order from a
    # database is not guaranteed — so it is stored rather than inferred.
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    tiers: Mapped[list["Tier"]] = relationship(
        back_populates="lash_set",
        cascade="all, delete-orphan",
        order_by="Tier.position",
    )

    __table_args__ = (CheckConstraint("position >= 0", name="ck_lash_sets_position"),)


class Tier(Base):
    """A volume within a set, e.g. "Mid volume" — what a client actually books."""

    __tablename__ = "tiers"

    id: Mapped[str] = mapped_column(_ID, primary_key=True)
    set_id: Mapped[str] = mapped_column(
        _ID, ForeignKey("lash_sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(80), nullable=False)

    # Whole Kenyan shillings. Prices here are whole shillings, so an integer
    # keeps floating-point error away from money entirely.
    amount_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    note: Mapped[str | None] = mapped_column(String(80), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    lash_set: Mapped[LashSet] = relationship(back_populates="tiers")

    __table_args__ = (
        CheckConstraint("amount_kes >= 0", name="ck_tiers_amount_non_negative"),
        CheckConstraint("minutes > 0", name="ck_tiers_minutes_positive"),
        CheckConstraint("position >= 0", name="ck_tiers_position"),
    )


class Addition(Base):
    """An optional extra that stacks on top of a set, e.g. removal or charms."""

    __tablename__ = "additions"

    id: Mapped[str] = mapped_column(_ID, primary_key=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    amount_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("amount_kes >= 0", name="ck_additions_amount_non_negative"),
        CheckConstraint("minutes > 0", name="ck_additions_minutes_positive"),
        CheckConstraint("position >= 0", name="ck_additions_position"),
    )
