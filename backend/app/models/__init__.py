"""
Importing every model here registers it on Base.metadata, which is what
Alembic autogenerate compares the database against.
"""

from app.models.catalogue import Addition, LashSet, Tier

__all__ = ["Addition", "LashSet", "Tier"]
