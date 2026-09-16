"""
memory_engine/embeddings/base.py

Base interface for embedding providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract interface for embedding engines."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate a vector embedding from a text string."""
        raise NotImplementedError
