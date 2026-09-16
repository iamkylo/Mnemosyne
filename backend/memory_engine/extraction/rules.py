"""
memory_engine/extraction/rules.py

Deterministic first-pass knowledge extraction.
"""

from __future__ import annotations

import re

from schemas.memory import KnowledgeFact, KnowledgeRelationship, MemoryKind, TextChunk

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_FILE_RE = re.compile(
    r"\b[\w./\\-]+\.(?:py|ts|tsx|js|jsx|md|json|yaml|yml|toml|sql|html|css)\b"
)
_DEPENDENCY_RE = re.compile(
    r"\b(?:fastapi|sqlalchemy|redis|qdrant|postgres|postgresql|openai|anthropic|ollama|groq|gemini|react|vite|pydantic)\b",
    re.I,
)

_KIND_PATTERNS: tuple[tuple[MemoryKind, re.Pattern[str]], ...] = (
    (
        MemoryKind.REQUIREMENT,
        re.compile(
            r"\b(requirement|required|acceptance|must support|user should|system should)\b",
            re.I,
        ),
    ),
    (
        MemoryKind.DECISION,
        re.compile(r"\b(decided|decision|choose|chosen|use|using)\b", re.I),
    ),
    (
        MemoryKind.TODO,
        re.compile(
            r"\b(todo|next|pending|later|follow up|need to|needs to|implement)\b", re.I
        ),
    ),
    (
        MemoryKind.BUG,
        re.compile(
            r"\b(bug|error|failure|failing|broken|regression|exception|issue)\b", re.I
        ),
    ),
    (
        MemoryKind.FIX,
        re.compile(r"\b(fix|fixed|resolved|patch|repair|workaround)\b", re.I),
    ),
    (
        MemoryKind.ARCHITECTURE,
        re.compile(
            r"\b(architecture|pipeline|service|repository|adapter|provider|module|layer)\b",
            re.I,
        ),
    ),
)


class RuleBasedKnowledgeExtractor:
    """Extract facts and relationships without relying on provider calls."""

    def extract(
        self, chunk: TextChunk
    ) -> tuple[list[KnowledgeFact], list[KnowledgeRelationship]]:
        facts: list[KnowledgeFact] = []
        relationships: list[KnowledgeRelationship] = []

        for sentence in _split_sentences(chunk.text):
            fact = self._extract_fact(sentence)
            if fact is not None:
                facts.append(fact)

            for file_path in _FILE_RE.findall(sentence):
                facts.append(
                    KnowledgeFact(
                        kind=MemoryKind.FILE_REFERENCE,
                        text=file_path,
                        confidence=0.95,
                        attributes={"source_sentence": sentence},
                    )
                )

            for dependency in dict.fromkeys(
                match.group(0).lower() for match in _DEPENDENCY_RE.finditer(sentence)
            ):
                facts.append(
                    KnowledgeFact(
                        kind=MemoryKind.DEPENDENCY,
                        text=dependency,
                        confidence=0.9,
                        attributes={"source_sentence": sentence},
                    )
                )

            relationships.extend(_extract_relationships(sentence))

        return _dedupe_facts(facts), _dedupe_relationships(relationships)

    def _extract_fact(self, sentence: str) -> KnowledgeFact | None:
        for kind, pattern in _KIND_PATTERNS:
            if pattern.search(sentence):
                return KnowledgeFact(
                    kind=kind,
                    text=sentence,
                    confidence=0.78 if kind != MemoryKind.DECISION else 0.84,
                )

        if len(sentence.split()) >= 8:
            return KnowledgeFact(
                kind=MemoryKind.GENERAL, text=sentence, confidence=0.55
            )
        return None


def _split_sentences(text: str) -> list[str]:
    return [
        part.strip(" -\t") for part in _SENTENCE_RE.split(text) if part.strip(" -\t")
    ]


def _extract_relationships(sentence: str) -> list[KnowledgeRelationship]:
    relationships: list[KnowledgeRelationship] = []
    relation_patterns = (
        (
            re.compile(r"\b(.+?)\s+(?:depends on|requires)\s+(.+?)\b", re.I),
            "depends_on",
        ),
        (re.compile(r"\b(.+?)\s+(?:uses|using)\s+(.+?)\b", re.I), "uses"),
        (
            re.compile(r"\b(.+?)\s+(?:updates|feeds|writes to)\s+(.+?)\b", re.I),
            "updates",
        ),
    )
    for pattern, relation in relation_patterns:
        match = pattern.search(sentence)
        if match:
            source = _compact_node(match.group(1))
            target = _compact_node(match.group(2))
            if source and target and source != target:
                relationships.append(
                    KnowledgeRelationship(
                        source=source,
                        relation=relation,
                        target=target,
                        confidence=0.7,
                    )
                )
    return relationships


def _compact_node(value: str) -> str:
    words = re.findall(r"[A-Za-z0-9_.\\/-]+", value)
    return " ".join(words[-5:]).strip().lower()


def _dedupe_facts(facts: list[KnowledgeFact]) -> list[KnowledgeFact]:
    seen: set[tuple[MemoryKind, str]] = set()
    unique: list[KnowledgeFact] = []
    for fact in facts:
        key = (fact.kind, fact.text.lower())
        if key not in seen:
            seen.add(key)
            unique.append(fact)
    return unique


def _dedupe_relationships(
    relationships: list[KnowledgeRelationship],
) -> list[KnowledgeRelationship]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[KnowledgeRelationship] = []
    for relationship in relationships:
        key = (relationship.source, relationship.relation, relationship.target)
        if key not in seen:
            seen.add(key)
            unique.append(relationship)
    return unique
