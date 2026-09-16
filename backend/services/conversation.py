"""
services/conversation.py

Conversation creation and retrieval.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db_session
from models.conversation import Conversation
from models.message import Message
from repositories.conversation import ConversationRepository
from schemas.conversations import ConversationCreateRequest, ConversationResponse


class ConversationService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ConversationRepository(session)

    async def create_conversation(
        self, request: ConversationCreateRequest
    ) -> ConversationResponse:
        conversation = Conversation(
            id=request.conversation_id,
            project_id=request.project_id,
            title=request.title,
            meta=request.metadata,
        )
        conversation = await self._repo.create(conversation)

        for index, message in enumerate(request.messages):
            message_model = Message(
                external_id=message.external_id,
                conversation_id=conversation.id,
                role=message.role.value,
                content=message.content,
                source_order=index,
                meta=message.metadata,
            )
            await self._repo.create_message(message_model)

        return ConversationResponse.model_validate(conversation)

    async def get_conversation(
        self, conversation_id: str
    ) -> ConversationResponse | None:
        conversation = await self._repo.get_by_id(conversation_id)
        return (
            ConversationResponse.model_validate(conversation) if conversation else None
        )

    async def list_conversations(self, project_id: str) -> list[ConversationResponse]:
        conversations = await self._repo.list_for_project(project_id)
        return [ConversationResponse.model_validate(item) for item in conversations]


def get_conversation_service(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationService:
    return ConversationService(session)
