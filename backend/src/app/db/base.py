"""SQLAlchemy declarative base and model metadata registry."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# Import models here so Alembic and metadata.create_all see them.
# Example (when domain models exist):
# from app.models.user import User  # noqa: F401
