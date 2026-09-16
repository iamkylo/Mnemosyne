"""
database/base.py

SQLAlchemy declarative base and common mixins.

Every ORM model will inherit from `Base`.
We also provide a `TimestampMixin` that automatically adds
`created_at` and `updated_at` to any model that includes it.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    """

    id: Any
    __name__: str

    # Generate __tablename__ automatically from class name
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # e.g. User -> users, Project -> projects (simple pluralization)
        # For a production app, you might use a more robust pluralizer.
        name = cls.__name__.lower()
        if name.endswith("y"):
            return name[:-1] + "ies"
        elif name.endswith("s"):
            return name + "es"
        return name + "s"


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns to a model.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
