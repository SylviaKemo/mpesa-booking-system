"""Catalogue tables: lash sets, their tiers, and additions.

Prices are whole-KES integers. Check constraints keep amounts non-negative and
durations positive at the database level, so bad data cannot be written even by
a path that skips the application.

Revision ID: 6267a8621d02
Revises: 64eb028d621d
Create Date: 2026-10-06 16:21:06.492379
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '6267a8621d02'
down_revision: str | None = '64eb028d621d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('additions',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('label', sa.String(length=80), nullable=False),
    sa.Column('amount_kes', sa.Integer(), nullable=False),
    sa.Column('minutes', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.CheckConstraint('amount_kes >= 0', name='ck_additions_amount_non_negative'),
    sa.CheckConstraint('minutes > 0', name='ck_additions_minutes_positive'),
    sa.CheckConstraint('position >= 0', name='ck_additions_position'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lash_sets',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('blurb', sa.Text(), nullable=False),
    sa.Column('image_url', sa.Text(), nullable=False),
    sa.Column('image_alt', sa.String(length=160), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.CheckConstraint('position >= 0', name='ck_lash_sets_position'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tiers',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('set_id', sa.String(length=32), nullable=False),
    sa.Column('label', sa.String(length=80), nullable=False),
    sa.Column('amount_kes', sa.Integer(), nullable=False),
    sa.Column('minutes', sa.Integer(), nullable=False),
    sa.Column('note', sa.String(length=80), nullable=True),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.CheckConstraint('amount_kes >= 0', name='ck_tiers_amount_non_negative'),
    sa.CheckConstraint('minutes > 0', name='ck_tiers_minutes_positive'),
    sa.CheckConstraint('position >= 0', name='ck_tiers_position'),
    sa.ForeignKeyConstraint(['set_id'], ['lash_sets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('tiers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tiers_set_id'), ['set_id'], unique=False)



def downgrade() -> None:
    with op.batch_alter_table('tiers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tiers_set_id'))

    op.drop_table('tiers')
    op.drop_table('lash_sets')
    op.drop_table('additions')
