"""M-Pesa deposit attempts.

One row per prompt rather than a column on the booking: a client may cancel and
try again, and the failures matter when someone asks why their money left but
the slot did not stick. checkout_request_id is unique because it is the
idempotency key for a callback Safaricom retries.

Revision ID: fe8a33eaf4a3
Revises: ea9235878302
Create Date: 2026-10-06 17:15:28.255462
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'fe8a33eaf4a3'
down_revision: str | None = 'ea9235878302'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('payments',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('booking_id', sa.Integer(), nullable=False),
    sa.Column('checkout_request_id', sa.String(length=64), nullable=False),
    sa.Column('merchant_request_id', sa.String(length=64), nullable=False),
    sa.Column('amount_kes', sa.Integer(), nullable=False),
    sa.Column('phone', sa.String(length=15), nullable=False),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('result_code', sa.Integer(), nullable=True),
    sa.Column('result_desc', sa.Text(), nullable=True),
    sa.Column('mpesa_receipt', sa.String(length=32), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint('amount_kes > 0', name='ck_payments_amount_positive'),
    sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('checkout_request_id')
    )
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_payments_booking_id'), ['booking_id'], unique=False)



def downgrade() -> None:
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_payments_booking_id'))

    op.drop_table('payments')
