"""
models/message.py

Persisted conversation messages.
"""

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_order: Mapped[int] = mapped_column(Integer, nullable=False)
    meta: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict)

    conversation = relationship(
        "Conversation", back_populates="messages", lazy="selectin"
    )
