"""
memory_engine/ranking/importance.py

Importance scoring for extracted memory candidates.
"""

from __future__ import annotations

from schemas.memory import KnowledgeFact, MemoryKind

_BASE_SCORES: dict[MemoryKind, float] = {
    MemoryKind.DECISION: 0.9,
    MemoryKind.REQUIREMENT: 0.88,
    MemoryKind.BUG: 0.82,
    MemoryKind.FIX: 0.8,
    MemoryKind.TODO: 0.78,
    MemoryKind.ARCHITECTURE: 0.76,
    MemoryKind.FILE_REFERENCE: 0.7,
    MemoryKind.DEPENDENCY: 0.65,
    MemoryKind.GENERAL: 0.48,
}


class ImportanceScorer:
    """Score memories by type, confidence, and information density."""

    def score(self, fact: KnowledgeFact) -> float:
        words = fact.text.split()
        density_bonus = min(0.08, len(set(word.lower() for word in words)) / 250)
        confidence_bonus = (fact.confidence - 0.5) * 0.18
        score = _BASE_SCORES[fact.kind] + density_bonus + confidence_bonus
        return round(max(0.0, min(1.0, score)), 3)
