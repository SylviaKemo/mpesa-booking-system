"""When a booking reached Shamim's calendar.

Null on a confirmed booking means the calendar has not got it yet, so the next
sync retries it. A timestamp rather than a flag, so "when did this land" has an
answer when a client says Shamim did not know they were coming.

Batch mode for SQLite, which cannot drop a column in place; the rebuild keeps
the partial uq_bookings_live_slot index (checked on upgrade and downgrade).

Revision ID: d43fc046a0a4
Revises: fe8a33eaf4a3
Create Date: 2026-10-07 19:12:44.959406
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'd43fc046a0a4'
down_revision: str | None = 'fe8a33eaf4a3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('calendar_synced_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_column('calendar_synced_at')
