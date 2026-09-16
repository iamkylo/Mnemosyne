"""
providers/local.py

Local provider adapter backed by deterministic hashing embeddings.
"""

from __future__ import annotations

from memory_engine.embeddings.hashing import HashingEmbeddingProvider
from providers.base import ProviderAdapter


class LocalProvider(ProviderAdapter):
    """Offline provider for deterministic embeddings during development."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        super().__init__(endpoint=endpoint, api_key=api_key, metadata=metadata)
        dimensions = int(self.metadata.get("dimensions", 384))
        self._embedder = HashingEmbeddingProvider(dimensions=dimensions)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embedder.embed(text) for text in texts]

    async def complete(self, prompt: str) -> str:
        raise NotImplementedError("Local completion support is not yet implemented.")
