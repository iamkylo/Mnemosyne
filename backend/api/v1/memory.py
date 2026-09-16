"""
api/v1/memory.py

Memory ingestion and retrieval endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from core.auth import get_current_user
from core.config import settings
from schemas.memory import (
    MemoryIngestRequest,
    MemoryIngestResult,
    MemoryResponse,
    KnowledgeRelationshipResponse,
)
from schemas.response import SuccessResponse, success
from services.memory import MemoryService, get_memory_service

router = APIRouter()
MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]
CurrentUserDep = Annotated[object, Depends(get_current_user)]


@router.post(
    "/ingest",
    summary="Process a conversation into structured memory",
    response_model=SuccessResponse[MemoryIngestResult],
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_conversation(
    request: MemoryIngestRequest,
    _: CurrentUserDep,
    memory_service: MemoryServiceDep,
) -> SuccessResponse[MemoryIngestResult]:
    """Transform conversation messages into chunks, memories, graph edges, and DNA."""
    result = await memory_service.ingest_conversation(request)
    return success(
        message="Conversation processed into structured memory",
        data=result,
        version=settings.app_version,
    )


@router.get(
    "/project/{project_id}",
    summary="List all memories for a project",
    response_model=SuccessResponse[list[MemoryResponse]],
)
async def list_project_memories(
    project_id: str,
    _: CurrentUserDep,
    memory_service: MemoryServiceDep,
) -> SuccessResponse[list[MemoryResponse]]:
    result = await memory_service.list_project_memories(project_id)
    return success(
        message="Project memories retrieved.",
        data=result,
        version=settings.app_version,
    )


@router.get(
    "/project/{project_id}/relationships",
    summary="List all knowledge relationships for a project",
    response_model=SuccessResponse[list[KnowledgeRelationshipResponse]],
)
async def list_project_relationships(
    project_id: str,
    _: CurrentUserDep,
    memory_service: MemoryServiceDep,
) -> SuccessResponse[list[KnowledgeRelationshipResponse]]:
    result = await memory_service.list_project_relationships(project_id)
    return success(
        message="Project relationships retrieved.",
        data=result,
        version=settings.app_version,
    )
