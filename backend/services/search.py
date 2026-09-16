from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db_session
from memory_engine.embeddings.hashing import HashingEmbeddingProvider
from memory_engine.retrieval.vector_store import QdrantVectorStore
from repositories.memory import MemoryRepository
from schemas.memory import MemoryCandidate, MemoryKind
from schemas.retrieval import MemoryReference, RetrievalRequest, RetrievalResult


class RetrievalService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = MemoryRepository(session)
        self._vector_store = QdrantVectorStore()
        self._embedder = HashingEmbeddingProvider()

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        # Load enabled providers to initialize ProviderRouter
        from providers.router import ProviderRouter
        from repositories.provider import ProviderConfigRepository
        from schemas.providers import ProviderConfigResponse

        provider_repo = ProviderConfigRepository(self._repo._session)
        enabled_configs = await provider_repo.list_enabled()
        router_configs = [
            ProviderConfigResponse.model_validate(c) for c in enabled_configs
        ]

        query_embedding = []
        if router_configs:
            try:
                router = ProviderRouter(router_configs)
                embeddings = await router.embed([request.query])
                if embeddings:
                    query_embedding = embeddings[0]
            except Exception:
                pass

        if not query_embedding:
            # Fallback to local hashing of dimension 384 (matching Qdrant collection)
            from memory_engine.embeddings.hashing import HashingEmbeddingProvider

            hashing_embedder = HashingEmbeddingProvider(dimensions=384)
            query_embedding = hashing_embedder.embed(request.query)

        # 1. Fetch from Vector Store (project-scoped)
        vector_candidates = await self._vector_store.search(
            query_embedding, project_id=request.project_id, top_k=request.top_k * 2
        )

        # 2. Fetch from DB Keyword Search (project-scoped)
        keyword_memories = await self._repo.search_memories_by_keyword(
            project_id=request.project_id, query=request.query, limit=request.top_k * 2
        )

        # Map both sources to a unified collection of memories
        unified_memories: dict[str, MemoryCandidate] = {}
        for cand in vector_candidates:
            unified_memories[cand.id] = cand

        for memory in keyword_memories:
            if memory.id not in unified_memories:
                unified_memories[memory.id] = MemoryCandidate(
                    id=memory.id,
                    project_id=memory.project_id,
                    conversation_id=memory.conversation_id or "",
                    chunk_id=memory.chunk_id or "",
                    kind=MemoryKind(memory.kind)
                    if isinstance(memory.kind, str)
                    else memory.kind,
                    text=memory.text,
                    importance=memory.importance,
                    confidence=memory.confidence,
                    embedding=[],
                    source_message_ids=memory.source_message_ids or [],
                    attributes=memory.attributes or {},
                )

        # Calculate RRF Scores
        # RRF(d) = sum_{m in matchers} 1 / (60 + rank_m(d))
        rrf_scores: dict[str, float] = {}
        k = 60.0

        for rank, cand in enumerate(vector_candidates, start=1):
            rrf_scores[cand.id] = rrf_scores.get(cand.id, 0.0) + (1.0 / (k + rank))

        for rank, memory in enumerate(keyword_memories, start=1):
            rrf_scores[memory.id] = rrf_scores.get(memory.id, 0.0) + (1.0 / (k + rank))

        # Sort keys by RRF score descending
        sorted_ids = sorted(
            rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True
        )
        final_candidates = [
            unified_memories[mid] for mid in sorted_ids[: request.top_k]
        ]

        # Fallback: if no search matches are found, retrieve top general project memories
        if not final_candidates:
            fallback_memories = await self._repo.list_top_memories_for_project(
                request.project_id, limit=request.top_k
            )
            final_candidates = [
                MemoryCandidate(
                    id=mem.id,
                    project_id=mem.project_id,
                    conversation_id=mem.conversation_id or "",
                    chunk_id=mem.chunk_id or "",
                    kind=MemoryKind(mem.kind)
                    if isinstance(mem.kind, str)
                    else mem.kind,
                    text=mem.text,
                    importance=mem.importance,
                    confidence=mem.confidence,
                    embedding=[],
                    source_message_ids=mem.source_message_ids or [],
                    attributes=mem.attributes or {},
                )
                for mem in fallback_memories
            ]

        # Convert to schema references
        references = [
            MemoryReference(
                id=cand.id,
                kind=cand.kind.value
                if isinstance(cand.kind, MemoryKind)
                else str(cand.kind),
                text=cand.text,
                importance=cand.importance,
                confidence=cand.confidence,
                source_message_ids=cand.source_message_ids,
                attributes=cand.attributes,
            )
            for cand in final_candidates
        ]

        context = "\n".join(f"[{ref.kind}] {ref.text}" for ref in references)
        return RetrievalResult(
            project_id=request.project_id,
            query=request.query,
            top_k=request.top_k,
            context=context,
            memories=references,
        )


def get_retrieval_service(
    session: AsyncSession = Depends(get_db_session),
) -> RetrievalService:
    return RetrievalService(session)
