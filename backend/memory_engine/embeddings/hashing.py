"""
memory_engine/embeddings/hashing.py

Stable local embeddings used until provider-backed embedding models are enabled.
"""

from __future__ import annotations

import hashlib
import math
import re

_TERM_RE = re.compile(r"[a-zA-Z0-9_./\\-]+")


class HashingEmbeddingProvider:
    """Create deterministic normalized vectors using feature hashing."""

    def __init__(self, dimensions: int = 64) -> None:
        if dimensions < 8:
            raise ValueError("dimensions must be at least 8.")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for term in _terms(text):
            digest = hashlib.blake2b(term.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [round(value / magnitude, 6) for value in vector]


def _terms(text: str) -> list[str]:
    return [match.group(0).lower() for match in _TERM_RE.finditer(text)]
