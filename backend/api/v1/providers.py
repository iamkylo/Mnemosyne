"""
api/v1/providers.py

AI provider configuration endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import get_current_user
from core.config import settings
from schemas.providers import (
    ProviderConfigCreateRequest,
    ProviderConfigResponse,
    ProviderConfigUpdateRequest,
    ProviderHealthResponse,
)
from schemas.response import SuccessResponse, success
from services.providers import ProviderService, get_provider_service

router = APIRouter()
ProviderServiceDep = Annotated[ProviderService, Depends(get_provider_service)]
CurrentUserDep = Annotated[object, Depends(get_current_user)]


@router.post(
    "",
    response_model=SuccessResponse[ProviderConfigResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_provider(
    request: ProviderConfigCreateRequest,
    _: CurrentUserDep,
    provider_service: ProviderServiceDep,
) -> SuccessResponse[ProviderConfigResponse]:
    return success(
        message="Provider added.",
        data=await provider_service.create_provider(request),
        version=settings.app_version,
    )


@router.get(
    "",
    response_model=SuccessResponse[list[ProviderConfigResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_providers(
    _: CurrentUserDep,
    provider_service: ProviderServiceDep,
) -> SuccessResponse[list[ProviderConfigResponse]]:
    return success(
        message="Provider configuration list retrieved.",
        data=await provider_service.list_providers(),
        version=settings.app_version,
    )


@router.get(
    "/{name}",
    response_model=SuccessResponse[ProviderConfigResponse],
    status_code=status.HTTP_200_OK,
)
async def get_provider(
    name: str,
    _: CurrentUserDep,
    provider_service: ProviderServiceDep,
) -> SuccessResponse[ProviderConfigResponse]:
    config = await provider_service.get_provider(name)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found."
        )
    return success(
        message="Provider configuration retrieved.",
        data=config,
        version=settings.app_version,
    )


@router.patch(
    "/{name}",
    response_model=SuccessResponse[ProviderConfigResponse],
    status_code=status.HTTP_200_OK,
)
async def update_provider(
    name: str,
    request: ProviderConfigUpdateRequest,
    _: CurrentUserDep,
    provider_service: ProviderServiceDep,
) -> SuccessResponse[ProviderConfigResponse]:
    try:
        config = await provider_service.update_provider(name, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return success(
        message="Provider configuration updated.",
        data=config,
        version=settings.app_version,
    )


@router.get(
    "/health",
    response_model=SuccessResponse[list[ProviderHealthResponse]],
    status_code=status.HTTP_200_OK,
)
async def provider_health(
    _: CurrentUserDep,
    provider_service: ProviderServiceDep,
) -> SuccessResponse[list[ProviderHealthResponse]]:
    return success(
        message="Provider health report.",
        data=await provider_service.provider_health(),
        version=settings.app_version,
    )
