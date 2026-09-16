"""
models/relationship.py

Knowledge graph relationships extracted from memory chunks.
"""

from sqlalchemy import ForeignKey, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class KnowledgeRelationship(Base, TimestampMixin):
    __tablename__ = "knowledge_relationships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversations.id"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(256), nullable=False)
    relation: Mapped[str] = mapped_column(String(128), nullable=False)
    target: Mapped[str] = mapped_column(String(256), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    meta: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict)

    conversation = relationship(
        "Conversation", back_populates="relationships", lazy="selectin"
    )
