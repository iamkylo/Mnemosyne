"""
workers/tasks.py

Background task definitions for long-running memory operations.

These tasks are executed asynchronously via FastAPI BackgroundTasks or
can be plugged into a Celery/RQ worker when horizontal scaling is needed.

Design note
-----------
Each task is a standalone async function accepting primitive arguments
(no SQLAlchemy objects) so they can be safely serialised and replayed.
"""

from __future__ import annotations

from loguru import logger

from schemas.memory import MemoryIngestRequest


# ─────────────────────────────────────────────────────────────────────────────
# Ingestion task
# ─────────────────────────────────────────────────────────────────────────────


async def run_memory_ingestion(
    request: MemoryIngestRequest,
    database_url: str,
) -> None:
    """
    Process a conversation into structured memory in the background.

    Creates its own database session so it does not depend on the
    request-scoped session from the HTTP handler.

    Args:
        request:      The memory ingest payload.
        database_url: SQLAlchemy async database URL.
    """
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from memory_engine.pipeline.async_ingestion import AsyncMemoryIngestionPipeline

    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine, expire_on_commit=False
    )

    try:
        async with session_factory() as session:
            pipeline = AsyncMemoryIngestionPipeline(session)
            result = await pipeline.process(request)
            logger.info(
                "Background ingestion complete: project={pid} chunks={c} memories={m}",
                pid=request.project_id,
                c=result.chunk_count,
                m=result.memory_count,
            )
    except Exception:
        logger.exception(
            "Background ingestion failed: project={pid} conversation={cid}",
            pid=request.project_id,
            cid=request.conversation_id,
        )
    finally:
        await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# DNA consolidation task
# ─────────────────────────────────────────────────────────────────────────────


async def consolidate_project_dna(project_id: str, database_url: str) -> None:
    """
    Re-aggregate the Project DNA from all stored memories.

    This is a periodic consolidation task that ensures the DNA remains
    accurate even if individual ingest runs produced noisy data.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from memory_engine.dna.patch import ProjectDnaPatchBuilder
    from models.memory import Memory
    from repositories.project import ProjectRepository
    from schemas.memory import MemoryCandidate, MemoryKind

    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine, expire_on_commit=False
    )

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Memory).where(Memory.project_id == project_id)
            )
            memories_orm = result.scalars().all()

            candidates = [
                MemoryCandidate(
                    id=m.id,
                    project_id=m.project_id,
                    conversation_id=m.conversation_id,
                    chunk_id=m.chunk_id,
                    kind=MemoryKind(m.kind),
                    text=m.text,
                    importance=m.importance,
                    confidence=m.confidence,
                    embedding=m.embedding or [],
                    source_message_ids=m.source_message_ids or [],
                    attributes=m.attributes or {},
                )
                for m in memories_orm
            ]

            builder = ProjectDnaPatchBuilder()
            patch = builder.build(project_id, candidates)

            repo = ProjectRepository(session)
            await repo.upsert_dna(project_id, patch.model_dump())

            logger.info(
                "DNA consolidation complete: project={pid} memories={count}",
                pid=project_id,
                count=len(candidates),
            )
    except Exception:
        logger.exception("DNA consolidation failed: project={pid}", pid=project_id)
    finally:
        await engine.dispose()
