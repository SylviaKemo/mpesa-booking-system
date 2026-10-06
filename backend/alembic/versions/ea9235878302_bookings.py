"""Bookings and their additions.

Amounts are frozen onto each row at booking time so a later catalogue change
cannot rewrite what someone agreed to pay. The slot index is partial — only a
live booking occupies a slot, so cancelling or expiring one frees it.

Revision ID: ea9235878302
Revises: d6c3cc9bd61a
Create Date: 2026-10-06 16:43:43.254853
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'ea9235878302'
down_revision: str | None = 'd6c3cc9bd61a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('bookings',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('reference', sa.String(length=16), nullable=False),
    sa.Column('booking_date', sa.Date(), nullable=False),
    sa.Column('slot_key', sa.String(length=8), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('payment_method', sa.String(length=10), nullable=False),
    sa.Column('tier_id', sa.String(length=32), nullable=False),
    sa.Column('amount_kes', sa.Integer(), nullable=False),
    sa.Column('deposit_kes', sa.Integer(), nullable=False),
    sa.Column('minutes', sa.Integer(), nullable=False),
    sa.Column('customer_name', sa.String(length=120), nullable=False),
    sa.Column('customer_phone', sa.String(length=15), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('hold_expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('amount_kes >= 0', name='ck_bookings_amount_non_negative'),
    sa.CheckConstraint('deposit_kes >= 0', name='ck_bookings_deposit_non_negative'),
    sa.CheckConstraint('minutes > 0', name='ck_bookings_minutes_positive'),
    sa.ForeignKeyConstraint(['tier_id'], ['tiers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('reference')
    )
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.create_index('uq_bookings_live_slot', ['booking_date', 'slot_key'], unique=True, sqlite_where=sa.text("status IN ('pending_payment', 'confirmed')"), postgresql_where=sa.text("status IN ('pending_payment', 'confirmed')"))

    op.create_table('booking_additions',
    sa.Column('booking_id', sa.Integer(), nullable=False),
    sa.Column('addition_id', sa.String(length=32), nullable=False),
    sa.Column('amount_kes', sa.Integer(), nullable=False),
    sa.Column('minutes', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['addition_id'], ['additions.id'], ),
    sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('booking_id', 'addition_id')
    )


def downgrade() -> None:
    op.drop_table('booking_additions')
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_index('uq_bookings_live_slot', sqlite_where=sa.text("status IN ('pending_payment', 'confirmed')"), postgresql_where=sa.text("status IN ('pending_payment', 'confirmed')"))

    op.drop_table('bookings')
