"""
repositories/memory.py

Data access for extracted memories, chunks, and relationships.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chunk import Chunk
from models.memory import Memory
from models.relationship import KnowledgeRelationship


class MemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_insert_chunks(self, chunks: list[Chunk]) -> None:
        self._session.add_all(chunks)
        await self._session.commit()

    async def bulk_insert_memories(self, memories: list[Memory]) -> None:
        self._session.add_all(memories)
        await self._session.commit()

    async def bulk_insert_relationships(
        self, relationships: list[KnowledgeRelationship]
    ) -> None:
        self._session.add_all(relationships)
        await self._session.commit()

    async def list_top_memories_for_project(
        self, project_id: str, limit: int = 5
    ) -> list[Memory]:
        statement = (
            select(Memory)
            .where(Memory.project_id == project_id)
            .order_by(Memory.importance.desc(), Memory.confidence.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def search_memories_by_keyword(
        self, project_id: str, query: str, limit: int = 10
    ) -> list[Memory]:
        statement = (
            select(Memory)
            .where(Memory.project_id == project_id, Memory.text.ilike(f"%{query}%"))
            .order_by(Memory.importance.desc(), Memory.confidence.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def list_all_memories_for_project(
        self, project_id: str, limit: int = 100
    ) -> list[Memory]:
        statement = (
            select(Memory)
            .where(Memory.project_id == project_id)
            .order_by(Memory.importance.desc(), Memory.confidence.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def list_relationships_for_project(
        self, project_id: str, limit: int = 100
    ) -> list[KnowledgeRelationship]:
        statement = (
            select(KnowledgeRelationship)
            .where(KnowledgeRelationship.project_id == project_id)
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()
