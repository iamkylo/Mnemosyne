"""
providers/base.py

Provider adapter interface for external AI services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ProviderAdapter(ABC):
    def __init__(
        self,
        endpoint: str | None,
        api_key: str | None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.metadata = metadata or {}

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        raise NotImplementedError
