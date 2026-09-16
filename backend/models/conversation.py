"""
models/conversation.py

Conversation sessions captured from AI platforms.
"""

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database.base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict)
    started_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    project = relationship("Project", back_populates="conversations", lazy="selectin")
    messages = relationship("Message", back_populates="conversation", lazy="selectin")
    chunks = relationship("Chunk", back_populates="conversation", lazy="selectin")
    memories = relationship("Memory", back_populates="conversation", lazy="selectin")
    relationships = relationship(
        "KnowledgeRelationship", back_populates="conversation", lazy="selectin"
    )
