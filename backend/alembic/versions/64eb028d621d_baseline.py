"""Baseline revision.

Intentionally empty: it anchors the migration chain so the first real schema
change has a parent to revise from. Tables arrive in the next slice.

Revision ID: 64eb028d621d
Revises: 
Create Date: 2026-10-06 15:50:17.849031
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '64eb028d621d'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
