import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from schemas.memory import MemoryCandidate, MemoryKind
from schemas.retrieval import RetrievalRequest
from services.search import RetrievalService


@pytest.mark.asyncio
async def test_hybrid_search_rrf() -> None:
    session = MagicMock()

    with (
        patch("services.search.MemoryRepository") as mock_repo_cls,
        patch(
            "repositories.provider.ProviderConfigRepository"
        ) as mock_provider_repo_cls,
        patch("services.search.QdrantVectorStore") as mock_vector_cls,
    ):
        mock_repo = mock_repo_cls.return_value
        mock_provider_repo = mock_provider_repo_cls.return_value
        mock_provider_repo.list_enabled = AsyncMock(return_value=[])
        mock_vector = mock_vector_cls.return_value

        # Setup vector results
        v_cand1 = MemoryCandidate(
            id="mem-1",
            project_id="proj-1",
            conversation_id="c-1",
            chunk_id="ch-1",
            kind=MemoryKind.REQUIREMENT,
            text="Vector requirement",
            importance=0.8,
            confidence=0.9,
            embedding=[0.1] * 384,
            source_message_ids=[],
            attributes={},
        )
        v_cand2 = MemoryCandidate(
            id="mem-2",
            project_id="proj-1",
            conversation_id="c-1",
            chunk_id="ch-1",
            kind=MemoryKind.DECISION,
            text="Shared decision text",
            importance=0.9,
            confidence=0.9,
            embedding=[0.1] * 384,
            source_message_ids=[],
            attributes={},
        )
        mock_vector.search = AsyncMock(return_value=[v_cand1, v_cand2])

        # Setup DB keyword results
        db_mem1 = MagicMock()
        db_mem1.id = "mem-2"  # Shared memory ID (present in both)
        db_mem1.project_id = "proj-1"
        db_mem1.conversation_id = "c-1"
        db_mem1.chunk_id = "ch-1"
        db_mem1.kind = "decision"
        db_mem1.text = "Shared decision text"
        db_mem1.importance = 0.9
        db_mem1.confidence = 0.9
        db_mem1.source_message_ids = []
        db_mem1.attributes = {}

        db_mem2 = MagicMock()
        db_mem2.id = "mem-3"  # Unique to DB keyword search
        db_mem2.project_id = "proj-1"
        db_mem2.conversation_id = "c-1"
        db_mem2.chunk_id = "ch-1"
        db_mem2.kind = "todo"
        db_mem2.text = "DB only keyword match"
        db_mem2.importance = 0.7
        db_mem2.confidence = 0.8
        db_mem2.source_message_ids = []
        db_mem2.attributes = {}

        mock_repo.search_memories_by_keyword = AsyncMock(
            return_value=[db_mem1, db_mem2]
        )

        service = RetrievalService(session)
        req = RetrievalRequest(project_id="proj-1", query="test query", top_k=5)
        res = await service.retrieve(req)

        assert len(res.memories) > 0
        ids = [m.id for m in res.memories]
        # Check if RRF merged them correctly
        assert "mem-2" in ids
        assert "mem-1" in ids
        assert "mem-3" in ids
