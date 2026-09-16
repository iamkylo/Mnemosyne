"""
services/memory.py

Business service for memory ingestion use cases.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db_session
from memory_engine.pipeline.async_ingestion import AsyncMemoryIngestionPipeline
from repositories.memory import MemoryRepository
from schemas.memory import MemoryIngestRequest, MemoryIngestResult


class MemoryService:
    """Application-facing facade over the memory engine."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._pipeline = AsyncMemoryIngestionPipeline(session)
        self._repo = MemoryRepository(session) if session is not None else None

    async def ingest_conversation(
        self,
        request: MemoryIngestRequest,
    ) -> MemoryIngestResult:
        return await self._pipeline.process(request)

    async def list_project_memories(self, project_id: str, limit: int = 100):
        if self._repo is None:
            raise RuntimeError("Database session not configured in MemoryService")
        return await self._repo.list_all_memories_for_project(project_id, limit)

    async def list_project_relationships(self, project_id: str, limit: int = 100):
        if self._repo is None:
            raise RuntimeError("Database session not configured in MemoryService")
        return await self._repo.list_relationships_for_project(project_id, limit)


def get_memory_service(
    session: AsyncSession = Depends(get_db_session),
) -> MemoryService:
    """Factory used by FastAPI dependencies."""
    return MemoryService(session)
