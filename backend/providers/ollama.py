"""
providers/ollama.py

Provider adapter for Ollama — local LLM inference server.

Ollama exposes an OpenAI-compatible REST API that also includes an
``/api/embeddings`` endpoint for generating dense vectors from local models.

Docs: https://github.com/ollama/ollama/blob/main/docs/api.md
"""

from __future__ import annotations

import httpx

from core.constants import HTTP_CLIENT_TIMEOUT
from providers.base import ProviderAdapter


_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
_DEFAULT_CHAT_MODEL = "llama3.2"
_DEFAULT_EMBED_MODEL = "nomic-embed-text"


class OllamaProvider(ProviderAdapter):
    """
    Ollama local inference adapter.

    ``endpoint`` should point to the running Ollama server
    (default: http://localhost:11434).
    ``api_key`` is not required for local Ollama.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        super().__init__(
            endpoint=endpoint or _DEFAULT_OLLAMA_BASE_URL,
            api_key=api_key,
            metadata=metadata or {},
        )
        self._chat_model: str = str(
            self.metadata.get("chat_model", _DEFAULT_CHAT_MODEL)
        )
        self._embed_model: str = str(
            self.metadata.get("embed_model", _DEFAULT_EMBED_MODEL)
        )
        self._timeout = int(self.metadata.get("timeout", HTTP_CLIENT_TIMEOUT))

    async def complete(self, prompt: str) -> str:
        """Send a generate request to Ollama and return the full response."""
        body = {
            "model": self._chat_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self.endpoint}/api/generate",
                json=body,
            )
            response.raise_for_status()
            return response.json()["response"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using the Ollama /api/embeddings endpoint."""
        results: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for text in texts:
                response = await client.post(
                    f"{self.endpoint}/api/embeddings",
                    json={"model": self._embed_model, "prompt": text},
                )
                response.raise_for_status()
                results.append(response.json()["embedding"])
        return results
