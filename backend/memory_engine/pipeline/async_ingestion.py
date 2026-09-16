"""
memory_engine/pipeline/async_ingestion.py

Integration-aware ingestion pipeline with persistence and vector storage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from memory_engine.pipeline.ingestion import MemoryIngestionPipeline
from memory_engine.retrieval.vector_store import QdrantVectorStore
from models.chunk import Chunk
from models.memory import Memory
from models.relationship import KnowledgeRelationship
from repositories.memory import MemoryRepository
import uuid
from loguru import logger

from memory_engine.pipeline.ingestion import _dedupe_memories, _dedupe_relationships
from repositories.project import ProjectRepository
from schemas.memory import MemoryCandidate, MemoryIngestRequest, MemoryIngestResult

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AsyncMemoryIngestionPipeline:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._pipeline = MemoryIngestionPipeline()
        self._repository = MemoryRepository(session) if session is not None else None
        self._vector_store = QdrantVectorStore() if session is not None else None

    async def process(self, request: MemoryIngestRequest) -> MemoryIngestResult:
        # 1. Run rule-based first-pass ingestion
        result = self._pipeline.process(request)

        # 2. Get active provider configurations to build ProviderRouter
        from providers.router import ProviderRouter
        from repositories.provider import ProviderConfigRepository
        from schemas.providers import ProviderConfigResponse

        router = None
        if self._repository is not None:
            provider_repo = ProviderConfigRepository(self._repository._session)
            enabled_configs = await provider_repo.list_enabled()
            router_configs = [
                ProviderConfigResponse.model_validate(c) for c in enabled_configs
            ]
            if router_configs:
                router = ProviderRouter(router_configs)

        # 3. Perform LLM-Enhanced second-pass extraction
        if router is not None:
            from memory_engine.extraction.llm import LlmKnowledgeExtractor
            from memory_engine.ranking.importance import ImportanceScorer

            logger.info("Executing second-pass LLM-enhanced knowledge extraction...")
            llm_extractor = LlmKnowledgeExtractor(router)
            scorer = ImportanceScorer()

            for chunk in result.chunks:
                llm_facts, llm_rels = await llm_extractor.extract(chunk)

                # Merge LLM facts
                for fact in llm_facts:
                    result.memories.append(
                        MemoryCandidate(
                            id=str(
                                uuid.uuid5(
                                    uuid.NAMESPACE_URL,
                                    f"{chunk.id}:{fact.kind}:{fact.text}",
                                )
                            ),
                            project_id=request.project_id,
                            conversation_id=request.conversation_id,
                            chunk_id=chunk.id,
                            kind=fact.kind,
                            text=fact.text,
                            importance=scorer.score(fact),
                            confidence=fact.confidence,
                            embedding=[],  # Will be generated below
                            source_message_ids=chunk.source_message_ids,
                            attributes=fact.attributes,
                        )
                    )
                # Merge relationships
                result.relationships.extend(llm_rels)

            # Deduplicate the combined results
            result.memories = _dedupe_memories(result.memories)
            result.relationships = _dedupe_relationships(result.relationships)

        # 4. Generate embeddings in batch (size = 384)
        memories_text = [m.text for m in result.memories]
        embeddings = []

        if router is not None and memories_text:
            try:
                embeddings = await router.embed(memories_text)
                logger.info(
                    f"Generated {len(embeddings)} provider-backed embeddings of size {len(embeddings[0])}."
                )
            except Exception as exc:
                logger.error(
                    f"Provider embedding failed: {exc}. Falling back to deterministic hashing."
                )

        # Fallback to local hashing of size 384
        if not embeddings and memories_text:
            from memory_engine.embeddings.hashing import HashingEmbeddingProvider

            hashing_embedder = HashingEmbeddingProvider(dimensions=384)
            embeddings = [hashing_embedder.embed(text) for text in memories_text]
            logger.info(
                f"Generated {len(embeddings)} fallback hashing embeddings of size 384."
            )

        # Assign embeddings back to candidate memories
        for memory, embedding in zip(result.memories, embeddings):
            memory.embedding = embedding

        # Re-build DNA patch based on the deduplicated & enhanced memories
        from memory_engine.dna.patch import ProjectDnaPatchBuilder

        dna_builder = ProjectDnaPatchBuilder()
        result.project_dna_patch = dna_builder.build(
            request.project_id, result.memories
        )

        # 5. Populate database models
        chunk_models = [
            Chunk(
                id=chunk.id,
                project_id=chunk.project_id,
                conversation_id=chunk.conversation_id,
                text=chunk.text,
                message_roles=[role.value for role in chunk.message_roles],
                source_message_ids=chunk.source_message_ids,
                token_estimate=chunk.token_estimate,
                meta=chunk.metadata,
            )
            for chunk in result.chunks
        ]

        memory_models = [
            Memory(
                id=memory.id,
                project_id=memory.project_id,
                conversation_id=memory.conversation_id,
                chunk_id=memory.chunk_id,
                kind=memory.kind.value,
                text=memory.text,
                importance=memory.importance,
                confidence=memory.confidence,
                embedding=memory.embedding,
                source_message_ids=memory.source_message_ids,
                attributes=memory.attributes,
            )
            for memory in result.memories
        ]

        relationship_models = [
            KnowledgeRelationship(
                project_id=request.project_id,
                conversation_id=request.conversation_id,
                source=relationship.source,
                relation=relationship.relation,
                target=relationship.target,
                confidence=relationship.confidence,
                meta={},
            )
            for relationship in result.relationships
        ]

        if self._repository is not None:
            session = self._repository._session
            from models.conversation import Conversation as DbConversation
            from models.message import Message as DbMessage
            from sqlalchemy import delete, select

            # Check and create conversation if missing
            stmt = select(DbConversation).where(
                DbConversation.id == request.conversation_id
            )
            res = await session.execute(stmt)
            conversation_exists = res.scalar_one_or_none() is not None

            if not conversation_exists:
                new_conv = DbConversation(
                    id=request.conversation_id,
                    project_id=request.project_id,
                    title=request.metadata.get(
                        "source_url",
                        f"Extension Session - {request.conversation_id[:8]}",
                    ),
                    meta=request.metadata or {},
                )
                session.add(new_conv)
                await session.flush()
                logger.info(
                    f"Created new conversation session: {request.conversation_id}"
                )
            else:
                # Update existing conversation metadata to ensure platform is stored
                stmt = select(DbConversation).where(
                    DbConversation.id == request.conversation_id
                )
                res = await session.execute(stmt)
                conv = res.scalar_one()
                current_meta = dict(conv.meta or {})
                updated = False
                for k, v in (request.metadata or {}).items():
                    if k not in current_meta or current_meta[k] != v:
                        current_meta[k] = v
                        updated = True
                if updated:
                    conv.meta = current_meta
                    session.add(conv)
                    await session.flush()

            # Clear existing data for this conversation to prevent duplicate primary keys / foreign keys
            await session.execute(
                delete(Memory).where(Memory.conversation_id == request.conversation_id)
            )
            await session.execute(
                delete(KnowledgeRelationship).where(
                    KnowledgeRelationship.conversation_id == request.conversation_id
                )
            )
            await session.execute(
                delete(Chunk).where(Chunk.conversation_id == request.conversation_id)
            )
            await session.execute(
                delete(DbMessage).where(
                    DbMessage.conversation_id == request.conversation_id
                )
            )
            await session.flush()

            # Insert message models
            message_models = [
                DbMessage(
                    external_id=msg.external_id,
                    conversation_id=request.conversation_id,
                    role=msg.role.value,
                    content=msg.content,
                    source_order=idx,
                    meta=msg.metadata or {},
                )
                for idx, msg in enumerate(request.messages)
            ]
            session.add_all(message_models)
            await session.flush()

            project_repo = ProjectRepository(session)
            await self._repository.bulk_insert_chunks(chunk_models)
            await self._repository.bulk_insert_memories(memory_models)
            await self._repository.bulk_insert_relationships(relationship_models)
            await project_repo.upsert_dna(
                request.project_id, result.project_dna_patch.model_dump()
            )

        if self._vector_store is not None:
            await self._vector_store.upsert_memories(result.memories)

        return result
