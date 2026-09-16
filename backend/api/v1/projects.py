"""
api/v1/projects.py

Project management endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import get_current_user
from core.config import settings
from schemas.projects import (
    ProjectCreateRequest,
    ProjectDnaResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from schemas.response import SuccessResponse, success
from services.project import ProjectService, get_project_service

router = APIRouter()
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
CurrentUserDep = Annotated[object, Depends(get_current_user)]


@router.post(
    "",
    response_model=SuccessResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    request: ProjectCreateRequest,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
) -> SuccessResponse[ProjectResponse]:
    response = await project_service.create_project(current_user.id, request)
    return success(
        message="Project created successfully.",
        data=response,
        version=settings.app_version,
    )


@router.patch(
    "/{project_id}",
    response_model=SuccessResponse[ProjectResponse],
    status_code=status.HTTP_200_OK,
)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    project_service: ProjectServiceDep,
) -> SuccessResponse[ProjectResponse]:
    try:
        response = await project_service.update_project(project_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return success(
        message="Project updated successfully.",
        data=response,
        version=settings.app_version,
    )


@router.get(
    "",
    response_model=SuccessResponse[list[ProjectResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_projects(
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
) -> SuccessResponse[list[ProjectResponse]]:
    response = await project_service.list_projects(current_user.id)
    return success(
        message="Project list retrieved.",
        data=response,
        version=settings.app_version,
    )


@router.get(
    "/{project_id}/dna",
    response_model=SuccessResponse[ProjectDnaResponse],
    status_code=status.HTTP_200_OK,
)
async def get_project_dna(
    project_id: str,
    project_service: ProjectServiceDep,
) -> SuccessResponse[ProjectDnaResponse]:
    response = await project_service.get_project_dna(project_id)
    if response is None:
        # Return empty DNA instead of 404 to avoid frontend errors for new projects
        response = ProjectDnaResponse(project_id=project_id)
    return success(
        message="Project DNA retrieved.",
        data=response,
        version=settings.app_version,
    )


@router.delete(
    "/{project_id}",
    response_model=SuccessResponse[bool],
    status_code=status.HTTP_200_OK,
)
async def delete_project(
    project_id: str,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
) -> SuccessResponse[bool]:
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found."
        )
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this project.",
        )
    success_deleted = await project_service.delete_project(project_id)
    return success(
        message="Project deleted successfully.",
        data=success_deleted,
        version=settings.app_version,
    )
