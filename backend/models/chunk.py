"""
models/chunk.py

Chunks generated from conversation data for embedding and extraction.
"""

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class Chunk(Base, TimestampMixin):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    message_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_message_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False)
    meta: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict)

    conversation = relationship("Conversation", back_populates="chunks", lazy="selectin")
