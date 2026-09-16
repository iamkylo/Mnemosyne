"""
schemas/conversations.py

Conversation API contracts.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.memory import ConversationMessage


class ConversationCreateRequest(BaseModel):
    project_id: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)
    title: str | None = None
    messages: list[ConversationMessage] = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class ConversationMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    content: str
    external_id: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, object] = Field(validation_alias="meta")


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str | None = None
    metadata: dict[str, object] = Field(validation_alias="meta")
    started_at: datetime
    ended_at: datetime | None = None
    messages: list[ConversationMessageResponse] | None = None
