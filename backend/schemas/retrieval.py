"""
schemas/retrieval.py

Semantic retrieval API contracts.
"""

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    project_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=25)


class MemoryReference(BaseModel):
    id: str
    kind: str
    text: str
    importance: float
    confidence: float
    source_message_ids: list[str]
    attributes: dict[str, object]


class RetrievalResult(BaseModel):
    project_id: str
    query: str
    top_k: int
    context: str
    memories: list[MemoryReference]
