"""
services/providers.py

Select and manage AI providers for routing and health checks.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db_session
from models.provider_config import ProviderConfig
from repositories.provider import ProviderConfigRepository
from schemas.providers import (
    ProviderConfigCreateRequest,
    ProviderConfigResponse,
    ProviderHealthResponse,
    ProviderConfigUpdateRequest,
)


class ProviderService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ProviderConfigRepository(session)

    async def list_providers(self) -> list[ProviderConfigResponse]:
        configs = await self._repo.list_enabled()
        return [ProviderConfigResponse.model_validate(config) for config in configs]

    async def get_provider(self, name: str) -> ProviderConfigResponse | None:
        config = await self._repo.get_by_name(name)
        return ProviderConfigResponse.model_validate(config) if config else None

    async def create_provider(
        self, request: ProviderConfigCreateRequest
    ) -> ProviderConfigResponse:
        config = await self._repo.create(
            config := ProviderConfig(
                name=request.name,
                endpoint=str(request.endpoint) if request.endpoint else None,
                api_key=request.api_key,
                priority=request.priority,
                enabled=request.enabled,
                meta=request.metadata,
            )
        )
        return ProviderConfigResponse.model_validate(config)

    async def update_provider(
        self, name: str, request: ProviderConfigUpdateRequest
    ) -> ProviderConfigResponse:
        config = await self._repo.get_by_name(name)
        if config is None:
            raise ValueError("Provider config not found.")
        patch = {
            ("meta" if k == "metadata" else k): v
            for k, v in request.model_dump(exclude_none=True).items()
        }
        config = await self._repo.update(config, patch)
        return ProviderConfigResponse.model_validate(config)

    async def provider_health(self) -> list[ProviderHealthResponse]:
        configs = await self._repo.list_enabled()
        return [
            ProviderHealthResponse(
                name=config.name,
                available=bool(config.api_key or config.endpoint),
                detail="Configured",
            )
            for config in configs
        ]


def get_provider_service(
    session: AsyncSession = Depends(get_db_session),
) -> ProviderService:
    return ProviderService(session)
