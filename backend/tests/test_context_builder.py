"""
tests/test_context_builder.py

Unit tests for the ContextBuilder and PromptOptimizer.
"""

from __future__ import annotations

import pytest

from memory_engine.context_builder import ContextBuilder
from memory_engine.prompt_optimizer import PromptOptimizer
from schemas.memory import MemoryCandidate, MemoryKind


def _make_candidate(
    kind: MemoryKind,
    text: str,
    importance: float = 0.8,
    confidence: float = 0.9,
) -> MemoryCandidate:
    return MemoryCandidate(
        id=f"mem-{hash(text) % 10000}",
        project_id="proj-test",
        conversation_id="conv-test",
        chunk_id="chunk-test",
        kind=kind,
        text=text,
        importance=importance,
        confidence=confidence,
        embedding=[0.1] * 384,
        source_message_ids=["msg-1"],
        attributes={},
    )


@pytest.fixture()
def sample_memories() -> list[MemoryCandidate]:
    return [
        _make_candidate(MemoryKind.DECISION, "Use FastAPI for the backend REST API."),
        _make_candidate(
            MemoryKind.REQUIREMENT, "The system must support JWT authentication."
        ),
        _make_candidate(
            MemoryKind.TODO, "Implement the Chrome extension content script."
        ),
        _make_candidate(MemoryKind.BUG, "Login endpoint returns 500 on missing email."),
        _make_candidate(
            MemoryKind.ARCHITECTURE, "Memory engine uses Qdrant for vector storage."
        ),
        _make_candidate(MemoryKind.DEPENDENCY, "fastapi", importance=0.5),
        _make_candidate(
            MemoryKind.GENERAL, "This is general context.", importance=0.35
        ),
    ]


class TestContextBuilder:
    def test_builds_markdown(self, sample_memories: list[MemoryCandidate]) -> None:
        builder = ContextBuilder()
        result = builder.build("proj-test", "Mnemosyne", sample_memories)
        assert "# Project Memory" in result.markdown

    def test_sections_contain_memories(
        self, sample_memories: list[MemoryCandidate]
    ) -> None:
        builder = ContextBuilder()
        result = builder.build("proj-test", "Mnemosyne", sample_memories)
        assert result.memory_count >= 1

    def test_respects_min_importance(self) -> None:
        memories = [
            _make_candidate(MemoryKind.GENERAL, "Low importance item.", importance=0.1),
        ]
        builder = ContextBuilder(min_importance=0.5)
        result = builder.build("proj-test", "Mnemosyne", memories)
        assert result.memory_count == 0

    def test_token_estimate_is_positive(
        self, sample_memories: list[MemoryCandidate]
    ) -> None:
        builder = ContextBuilder()
        result = builder.build("proj-test", "Mnemosyne", sample_memories)
        assert result.token_estimate > 0

    def test_respects_token_budget(
        self, sample_memories: list[MemoryCandidate]
    ) -> None:
        builder = ContextBuilder(max_tokens=50)
        result = builder.build("proj-test", "Mnemosyne", sample_memories)
        assert result.token_estimate <= 60  # slight tolerance for header

    def test_empty_memories_returns_header_only(self) -> None:
        builder = ContextBuilder()
        result = builder.build("proj-test", "Mnemosyne", [])
        assert result.memory_count == 0
        assert "# Project Memory" in result.markdown


class TestPromptOptimizer:
    def test_adds_injection_header(
        self, sample_memories: list[MemoryCandidate]
    ) -> None:
        builder = ContextBuilder()
        ctx = builder.build("proj-test", "Mnemosyne", sample_memories)
        optimizer = PromptOptimizer()
        optimized = optimizer.optimize(ctx.markdown)
        assert "structured summary" in optimized.lower()

    def test_deduplicates_bullets(self) -> None:
        optimizer = PromptOptimizer(deduplicate=True)
        text = "## Section\n- Bullet one\n- Bullet one\n- Bullet two"
        result = optimizer.optimize(text)
        assert result.count("- Bullet one") == 1

    def test_truncates_to_token_limit(self) -> None:
        optimizer = PromptOptimizer(max_tokens=10, injection_header="")
        long_text = "x" * 1000
        result = optimizer.optimize(long_text)
        assert len(result) < 1000

    def test_token_estimate_positive(self) -> None:
        optimizer = PromptOptimizer()
        assert optimizer.token_estimate("Hello world") > 0
