"""
models/project_dna.py

Project DNA stores persistent, aggregated project memory summaries.
"""

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class ProjectDna(Base, TimestampMixin):
    __tablename__ = "project_dna"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    dna: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)

    project = relationship("Project", lazy="selectin")
