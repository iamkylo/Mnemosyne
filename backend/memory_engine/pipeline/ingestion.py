"""
memory_engine/pipeline/ingestion.py

Orchestrates the complete deterministic memory ingestion pipeline.
"""

from __future__ import annotations

import uuid

from memory_engine.chunking.text import ConversationChunker
from memory_engine.dna.patch import ProjectDnaPatchBuilder
from memory_engine.embeddings.hashing import HashingEmbeddingProvider
from memory_engine.extraction.rules import RuleBasedKnowledgeExtractor
from memory_engine.ranking.importance import ImportanceScorer
from schemas.memory import MemoryCandidate, MemoryIngestRequest, MemoryIngestResult


class MemoryIngestionPipeline:
    """Run cleaning, chunking, extraction, scoring, embeddings, and DNA patching."""

    def __init__(
        self,
        chunker: ConversationChunker | None = None,
        extractor: RuleBasedKnowledgeExtractor | None = None,
        embedder: HashingEmbeddingProvider | None = None,
        scorer: ImportanceScorer | None = None,
        dna_builder: ProjectDnaPatchBuilder | None = None,
    ) -> None:
        self._chunker = chunker or ConversationChunker()
        self._extractor = extractor or RuleBasedKnowledgeExtractor()
        self._embedder = embedder or HashingEmbeddingProvider()
        self._scorer = scorer or ImportanceScorer()
        self._dna_builder = dna_builder or ProjectDnaPatchBuilder()

    def process(self, request: MemoryIngestRequest) -> MemoryIngestResult:
        chunks = self._chunker.chunk(request)
        memories: list[MemoryCandidate] = []
        relationships = []

        for chunk in chunks:
            facts, chunk_relationships = self._extractor.extract(chunk)
            relationships.extend(chunk_relationships)
            for fact in facts:
                memories.append(
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
                        importance=self._scorer.score(fact),
                        confidence=fact.confidence,
                        embedding=self._embedder.embed(fact.text),
                        source_message_ids=chunk.source_message_ids,
                        attributes=fact.attributes,
                    )
                )

        memories = sorted(
            _dedupe_memories(memories),
            key=lambda memory: (memory.importance, memory.confidence),
            reverse=True,
        )
        relationships = _dedupe_relationships(relationships)
        dna_patch = self._dna_builder.build(request.project_id, memories)

        return MemoryIngestResult(
            project_id=request.project_id,
            conversation_id=request.conversation_id,
            chunk_count=len(chunks),
            memory_count=len(memories),
            relationship_count=len(relationships),
            chunks=chunks,
            memories=memories,
            relationships=relationships,
            project_dna_patch=dna_patch,
        )


def _dedupe_memories(memories: list[MemoryCandidate]) -> list[MemoryCandidate]:
    seen: set[tuple[str, str]] = set()
    unique: list[MemoryCandidate] = []
    for memory in memories:
        key = (memory.kind.value, memory.text.lower())
        if key not in seen:
            seen.add(key)
            unique.append(memory)
    return unique


def _dedupe_relationships(relationships):
    seen: set[tuple[str, str, str]] = set()
    unique = []
    for relationship in relationships:
        key = (relationship.source, relationship.relation, relationship.target)
        if key not in seen:
            seen.add(key)
            unique.append(relationship)
    return unique
