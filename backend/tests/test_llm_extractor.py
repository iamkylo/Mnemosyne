import pytest
from unittest.mock import AsyncMock, MagicMock

from memory_engine.extraction.llm import LlmKnowledgeExtractor
from schemas.memory import MessageRole, MemoryKind, TextChunk


@pytest.mark.asyncio
async def test_llm_extractor_success() -> None:
    router = MagicMock()
    router.complete = AsyncMock(
        return_value="""
        {
          "facts": [
            {
              "kind": "requirement",
              "text": "System must support JWT tokens",
              "confidence": 0.95
            }
          ],
          "relationships": [
            {
              "source": "jwt",
              "relation": "depends_on",
              "target": "auth",
              "confidence": 0.90
            }
          ]
        }
        """
    )

    extractor = LlmKnowledgeExtractor(router)
    chunk = TextChunk(
        id="chunk-1",
        project_id="proj-1",
        conversation_id="c-1",
        text="Need JWT tokens for auth.",
        message_roles=[MessageRole.USER],
        source_message_ids=["msg-1"],
        token_estimate=5,
    )

    facts, rels = await extractor.extract(chunk)

    assert len(facts) == 1
    assert facts[0].kind == MemoryKind.REQUIREMENT
    assert facts[0].text == "System must support JWT tokens"
    assert facts[0].confidence == 0.95

    assert len(rels) == 1
    assert rels[0].source == "jwt"
    assert rels[0].relation == "depends_on"
    assert rels[0].target == "auth"


@pytest.mark.asyncio
async def test_llm_extractor_parse_failure() -> None:
    router = MagicMock()
    router.complete = AsyncMock(return_value="invalid json")

    extractor = LlmKnowledgeExtractor(router)
    chunk = TextChunk(
        id="chunk-1",
        project_id="proj-1",
        conversation_id="c-1",
        text="Just text.",
        message_roles=[MessageRole.USER],
        source_message_ids=["msg-1"],
        token_estimate=2,
    )

    facts, rels = await extractor.extract(chunk)

    # Should gracefully capture exception and return empty lists
    assert len(facts) == 0
    assert len(rels) == 0
