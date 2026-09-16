"""
schemas/projects.py

Project and project DNA API contracts.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateRequest(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    metadata: dict[str, object] | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    owner_id: int
    metadata: dict[str, object] = Field(validation_alias="meta")
    is_active: bool
    created_at: datetime


class ProjectDnaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: str
    objectives: list[str]
    decisions: list[str]
    pending_tasks: list[str]
    bugs: list[str]
    fixes: list[str]
    file_references: list[str]
    dependencies: list[str]
