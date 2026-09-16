"""
providers/router.py

Provider selection and failover logic.
"""

from __future__ import annotations

import logging
from typing import Iterable

from providers.base import ProviderAdapter
from providers.groq import GroqProvider
from providers.huggingface import HuggingFaceProvider
from providers.local import LocalProvider
from providers.ollama import OllamaProvider
from providers.openrouter import OpenRouterProvider
from schemas.providers import ProviderConfigResponse

logger = logging.getLogger(__name__)


_PROVIDER_MAP: dict[str, type[ProviderAdapter]] = {
    "local": LocalProvider,
    "hashing": LocalProvider,
    "groq": GroqProvider,
    "openrouter": OpenRouterProvider,
    "ollama": OllamaProvider,
    "huggingface": HuggingFaceProvider,
}


class ProviderRouter:
    """Choose the best available provider, with automatic failover."""

    def __init__(self, configs: Iterable[ProviderConfigResponse]) -> None:
        self._adapters = [
            self._create_adapter(config) for config in configs if config.enabled
        ]

    def _create_adapter(self, config: ProviderConfigResponse) -> ProviderAdapter:
        adapter_cls = _PROVIDER_MAP.get(config.name.lower())
        if adapter_cls is None:
            raise ValueError(f"Unknown provider {config.name}")
        return adapter_cls(
            endpoint=config.endpoint, api_key=config.api_key, metadata=config.metadata
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        last_error: Exception | None = None
        for adapter in self._adapters:
            try:
                return await adapter.embed(texts)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Provider %s failed: %s", type(adapter).__name__, str(exc)
                )
                continue

        if last_error:
            raise last_error

        raise RuntimeError("No provider adapters are configured.")

    async def complete(self, prompt: str) -> str:
        last_error: Exception | None = None
        for adapter in self._adapters:
            try:
                return await adapter.complete(prompt)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Provider %s failed: %s", type(adapter).__name__, str(exc)
                )
                continue

        if last_error:
            raise last_error

        raise RuntimeError("No provider adapters are configured.")
