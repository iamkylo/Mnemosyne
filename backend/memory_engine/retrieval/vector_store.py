"""
memory_engine/retrieval/vector_store.py

Client wrapper for Qdrant vector persistence and search.
"""

from __future__ import annotations

import asyncio

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from core.config import settings
from schemas.memory import MemoryCandidate


class QdrantVectorStore:
    """Qdrant-backed vector store for memory embeddings."""

    COLLECTION_NAME = "mnemosyne_memories"

    def __init__(self) -> None:
        self._client = QdrantClient(
            url=settings.qdrant_url, api_key=settings.qdrant_api_key or None
        )
        self._collection_checked = False

    def _ensure_collection_sync(self) -> None:
        target_size = 384
        try:
            info = self._client.get_collection(self.COLLECTION_NAME)
            # Access Qdrant remote collection size param safely
            # Note: depending on qdrant-client version, it is nested inside vectors config
            current_size = 0
            if hasattr(info.config.params.vectors, "size"):
                current_size = info.config.params.vectors.size
            elif isinstance(info.config.params.vectors, dict):
                current_size = info.config.params.vectors.get("size", 0)

            if current_size != target_size:
                self._client.recreate_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=rest.VectorParams(
                        size=target_size, distance=rest.Distance.COSINE
                    ),
                )
        except Exception:
            self._client.recreate_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=rest.VectorParams(
                    size=target_size, distance=rest.Distance.COSINE
                ),
            )

        try:
            self._client.create_payload_index(
                collection_name=self.COLLECTION_NAME,
                field_name="project_id",
                field_schema=rest.PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass

    async def _ensure_collection(self) -> None:
        if not self._collection_checked:
            await asyncio.to_thread(self._ensure_collection_sync)
            self._collection_checked = True

    async def upsert_memories(self, memories: list[MemoryCandidate]) -> None:
        await self._ensure_collection()
        points = [
            rest.PointStruct(
                id=memory.id,
                vector=memory.embedding,
                payload={
                    "project_id": memory.project_id,
                    "conversation_id": memory.conversation_id,
                    "kind": memory.kind.value,
                    "text": memory.text,
                    "importance": memory.importance,
                    "confidence": memory.confidence,
                    "source_message_ids": memory.source_message_ids,
                    "attributes": memory.attributes,
                },
            )
            for memory in memories
        ]
        await asyncio.to_thread(
            self._client.upsert,
            collection_name=self.COLLECTION_NAME,
            points=points,
        )

    async def search(
        self,
        query_embedding: list[float],
        project_id: str | None = None,
        top_k: int = 5,
    ) -> list[MemoryCandidate]:
        await self._ensure_collection()
        query_filter = None
        if project_id:
            query_filter = rest.Filter(
                must=[
                    rest.FieldCondition(
                        key="project_id",
                        match=rest.MatchValue(value=project_id),
                    )
                ]
            )

        response = await asyncio.to_thread(
            self._client.search,
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        memories: list[MemoryCandidate] = []
        for point in response:
            payload = point.payload or {}
            memories.append(
                MemoryCandidate(
                    id=str(point.id),
                    project_id=str(payload.get("project_id", "")),
                    conversation_id=str(payload.get("conversation_id", "")),
                    chunk_id="",
                    kind=payload.get("kind", "general"),
                    text=str(payload.get("text", "")),
                    importance=float(payload.get("importance", 0.0)),
                    confidence=float(payload.get("confidence", 0.0)),
                    embedding=query_embedding,
                    source_message_ids=payload.get("source_message_ids", []),
                    attributes=payload.get("attributes", {}),
                )
            )
        return memories

    async def delete_memories_by_project(self, project_id: str) -> None:
        await self._ensure_collection()
        query_filter = rest.Filter(
            must=[
                rest.FieldCondition(
                    key="project_id",
                    match=rest.MatchValue(value=project_id),
                )
            ]
        )
        await asyncio.to_thread(
            self._client.delete,
            collection_name=self.COLLECTION_NAME,
            points_selector=query_filter,
        )
