"""
providers/openrouter.py

Provider adapter for OpenRouter.ai — a unified gateway to 200+ LLMs.

OpenRouter exposes an OpenAI-compatible API so the adapter mirrors the
Groq implementation but points to the OpenRouter base URL.

Docs: https://openrouter.ai/docs
"""

from __future__ import annotations

import httpx

from core.constants import HTTP_CLIENT_TIMEOUT
from providers.base import ProviderAdapter


_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_CHAT_MODEL = "meta-llama/llama-3.1-70b-instruct"


class OpenRouterProvider(ProviderAdapter):
    """
    OpenRouter adapter (OpenAI-compatible).

    ``api_key`` must be an OpenRouter API key (sk-or-...).
    ``endpoint`` defaults to the OpenRouter base URL.
    ``metadata["chat_model"]`` controls which model is used.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        super().__init__(
            endpoint=endpoint or _OPENROUTER_BASE_URL,
            api_key=api_key,
            metadata=metadata or {},
        )
        self._chat_model: str = str(
            self.metadata.get("chat_model", _DEFAULT_CHAT_MODEL)
        )
        self._timeout = int(self.metadata.get("timeout", HTTP_CLIENT_TIMEOUT))

    async def complete(self, prompt: str) -> str:
        """Submit a chat completion request via OpenRouter."""
        if not self.api_key:
            raise ValueError("OpenRouter API key is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mnemosyne.ai",
            "X-Title": "Mnemosyne",
        }
        body = {
            "model": self._chat_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 2048,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self.endpoint}/chat/completions",
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """OpenRouter does not offer an embedding endpoint; use local fallback."""
        from memory_engine.embeddings.hashing import HashingEmbeddingProvider

        embedder = HashingEmbeddingProvider()
        return [embedder.embed(text) for text in texts]
