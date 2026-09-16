"""
services/project.py

Project lifecycle management.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db_session
from models.project import Project
from repositories.project import ProjectRepository
from schemas.projects import (
    ProjectCreateRequest,
    ProjectDnaResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ProjectRepository(session)

    async def create_project(
        self, owner_id: int, request: ProjectCreateRequest
    ) -> ProjectResponse:
        project = Project(
            id=request.id,
            name=request.name,
            description=request.description,
            owner_id=owner_id,
            meta={},
        )
        project = await self._repo.create(project)
        return ProjectResponse.model_validate(project)

    async def update_project(
        self, project_id: str, values: ProjectUpdateRequest
    ) -> ProjectResponse:
        project = await self._repo.get_by_id(project_id)
        if project is None:
            raise ValueError("Project not found.")
        patch = {
            ("meta" if k == "metadata" else k): v
            for k, v in values.model_dump(exclude_none=True).items()
        }
        project = await self._repo.update(project, patch)
        return ProjectResponse.model_validate(project)

    async def get_project(self, project_id: str) -> ProjectResponse | None:
        project = await self._repo.get_by_id(project_id)
        return ProjectResponse.model_validate(project) if project else None

    async def list_projects(self, owner_id: int) -> list[ProjectResponse]:
        projects = await self._repo.list_for_owner(owner_id)
        return [ProjectResponse.model_validate(project) for project in projects]

    async def get_project_dna(self, project_id: str) -> ProjectDnaResponse | None:
        dna = await self._repo.get_dna(project_id)
        if not dna:
            return None
        dna_dict = {k: v for k, v in dna.dna.items() if k != "project_id"}
        return ProjectDnaResponse(project_id=project_id, **dna_dict)

    async def upsert_project_dna(
        self, project_id: str, dna: dict[str, object]
    ) -> ProjectDnaResponse:
        dna_model = await self._repo.upsert_dna(project_id, dna)
        dna_dict = {k: v for k, v in dna_model.dna.items() if k != "project_id"}
        return ProjectDnaResponse(project_id=project_id, **dna_dict)

    async def delete_project(self, project_id: str) -> bool:
        from memory_engine.retrieval.vector_store import QdrantVectorStore
        import logging

        logger = logging.getLogger("mnemosyne")
        try:
            vector_store = QdrantVectorStore()
            await vector_store.delete_memories_by_project(project_id)
        except Exception as e:
            logger.error(
                f"Failed to clear Qdrant vectors for project {project_id}: {e}"
            )
        return await self._repo.delete(project_id)


def get_project_service(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectService:
    return ProjectService(session)
