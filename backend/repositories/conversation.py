"""
repositories/conversation.py

Data access for conversations and persisted messages.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.conversation import Conversation
from models.message import Message


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        statement = select(Conversation).where(Conversation.id == conversation_id)
        result = await self._session.execute(statement)
        return result.scalars().first()

    async def create(self, conversation: Conversation) -> Conversation:
        self._session.add(conversation)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def list_for_project(self, project_id: str) -> list[Conversation]:
        statement = (
            select(Conversation)
            .where(Conversation.project_id == project_id)
            .order_by(Conversation.started_at.desc())
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def create_message(self, message: Message) -> Message:
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message
