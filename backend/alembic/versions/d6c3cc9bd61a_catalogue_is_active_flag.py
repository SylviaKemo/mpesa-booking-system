"""Add is_active to catalogue tables.

Withdrawn items are deactivated rather than deleted so bookings that reference
them keep resolving. The server default backfills existing rows as active; sa.true() is used
rather than a literal 1 because Postgres rejects an integer default on a
boolean column.

Revision ID: d6c3cc9bd61a
Revises: 6267a8621d02
Create Date: 2026-10-06 16:32:48.521118
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'd6c3cc9bd61a'
down_revision: str | None = '6267a8621d02'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('additions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False))

    with op.batch_alter_table('lash_sets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False))

    with op.batch_alter_table('tiers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False))



def downgrade() -> None:
    with op.batch_alter_table('tiers', schema=None) as batch_op:
        batch_op.drop_column('is_active')

    with op.batch_alter_table('lash_sets', schema=None) as batch_op:
        batch_op.drop_column('is_active')

    with op.batch_alter_table('additions', schema=None) as batch_op:
        batch_op.drop_column('is_active')

