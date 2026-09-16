"""
tests/test_memory_ingestion.py

Unit tests for the deterministic memory ingestion pipeline.
"""

from __future__ import annotations

import pytest

from memory_engine.pipeline.ingestion import MemoryIngestionPipeline
from schemas.memory import (
    ConversationMessage,
    MemoryIngestRequest,
    MemoryKind,
    MessageRole,
)


@pytest.fixture()
def pipeline() -> MemoryIngestionPipeline:
    return MemoryIngestionPipeline()


@pytest.fixture()
def simple_request() -> MemoryIngestRequest:
    return MemoryIngestRequest(
        project_id="proj-001",
        conversation_id="conv-001",
        messages=[
            ConversationMessage(
                role=MessageRole.USER,
                content="We decided to use FastAPI for the backend because it supports async.",
            ),
            ConversationMessage(
                role=MessageRole.ASSISTANT,
                content=(
                    "Good choice. FastAPI uses SQLAlchemy for database access. "
                    "You need to implement the authentication module next. "
                    "There is a bug in the login endpoint — it returns 500 when email is missing."
                ),
            ),
        ],
    )


class TestMemoryIngestionPipeline:
    def test_returns_result_with_chunks(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        assert result.project_id == "proj-001"
        assert result.conversation_id == "conv-001"
        assert result.chunk_count >= 1

    def test_extracts_memories(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        assert result.memory_count >= 1

    def test_extracts_decision(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        kinds = {m.kind for m in result.memories}
        assert MemoryKind.DECISION in kinds

    def test_extracts_bug(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        kinds = {m.kind for m in result.memories}
        assert MemoryKind.BUG in kinds

    def test_extracts_dependency(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        kinds = {m.kind for m in result.memories}
        assert MemoryKind.DEPENDENCY in kinds

    def test_memories_have_valid_importance(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        for memory in result.memories:
            assert 0.0 <= memory.importance <= 1.0

    def test_memories_have_valid_confidence(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        for memory in result.memories:
            assert 0.0 <= memory.confidence <= 1.0

    def test_embeddings_generated(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        for memory in result.memories:
            assert len(memory.embedding) > 0

    def test_memories_sorted_by_importance_desc(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        importances = [m.importance for m in result.memories]
        assert importances == sorted(importances, reverse=True)

    def test_no_duplicate_memories(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        ids = [m.id for m in result.memories]
        assert len(ids) == len(set(ids))

    def test_dna_patch_has_project_id(
        self, pipeline: MemoryIngestionPipeline, simple_request: MemoryIngestRequest
    ) -> None:
        result = pipeline.process(simple_request)
        assert result.project_dna_patch.project_id == "proj-001"

    def test_empty_conversation_raises(self, pipeline: MemoryIngestionPipeline) -> None:
        with pytest.raises(Exception):
            MemoryIngestRequest(
                project_id="proj-001",
                conversation_id="conv-001",
                messages=[],
            )
