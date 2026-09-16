"""
schemas/memory.py

API and service contracts for memory ingestion.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageRole(str, Enum):
    """Supported conversation speaker roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MemoryKind(str, Enum):
    """Knowledge categories stored by the memory engine."""

    REQUIREMENT = "requirement"
    DECISION = "decision"
    TODO = "todo"
    BUG = "bug"
    FIX = "fix"
    FILE_REFERENCE = "file_reference"
    DEPENDENCY = "dependency"
    ARCHITECTURE = "architecture"
    GENERAL = "general"


class ConversationMessage(BaseModel):
    """Single message captured from an AI conversation."""

    role: MessageRole
    content: str = Field(min_length=1)
    external_id: str | None = Field(default=None)
    created_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def _strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message content cannot be blank.")
        return stripped


class MemoryIngestRequest(BaseModel):
    """Conversation payload submitted for memory processing."""

    project_id: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)
    messages: list[ConversationMessage] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TextChunk(BaseModel):
    """Normalized chunk generated from conversation text."""

    id: str
    project_id: str
    conversation_id: str
    text: str
    message_roles: list[MessageRole]
    source_message_ids: list[str]
    token_estimate: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeFact(BaseModel):
    """Structured fact extracted from a chunk."""

    kind: MemoryKind
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    attributes: dict[str, Any] = Field(default_factory=dict)


class KnowledgeRelationship(BaseModel):
    """Directed relationship between extracted concepts."""

    source: str
    relation: str
    target: str
    confidence: float = Field(ge=0.0, le=1.0)


class MemoryCandidate(BaseModel):
    """Persistable memory item produced by the ingestion pipeline."""

    id: str
    project_id: str
    conversation_id: str
    chunk_id: str
    kind: MemoryKind
    text: str
    importance: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    embedding: list[float]
    source_message_ids: list[str]
    attributes: dict[str, Any] = Field(default_factory=dict)


class ProjectDnaPatch(BaseModel):
    """Incremental project DNA update inferred from one ingest run."""

    project_id: str
    objectives: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    pending_tasks: list[str] = Field(default_factory=list)
    bugs: list[str] = Field(default_factory=list)
    fixes: list[str] = Field(default_factory=list)
    file_references: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class MemoryIngestResult(BaseModel):
    """Complete deterministic output of the memory ingestion pipeline."""

    project_id: str
    conversation_id: str
    chunk_count: int
    memory_count: int
    relationship_count: int
    chunks: list[TextChunk]
    memories: list[MemoryCandidate]
    relationships: list[KnowledgeRelationship]
    project_dna_patch: ProjectDnaPatch


class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    conversation_id: str
    chunk_id: str
    kind: str
    text: str
    importance: float
    confidence: float
    source_message_ids: list[str]
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class KnowledgeRelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: str
    conversation_id: str | None = None
    source: str
    relation: str
    target: str
    confidence: float
    metadata: dict[str, Any] = Field(validation_alias="meta")
    created_at: datetime
    updated_at: datetime
