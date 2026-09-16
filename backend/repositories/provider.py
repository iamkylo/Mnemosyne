"""
repositories/provider.py

Data access for AI provider configurations.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.provider_config import ProviderConfig


class ProviderConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_enabled(self) -> list[ProviderConfig]:
        statement = (
            select(ProviderConfig)
            .where(ProviderConfig.enabled.is_(True))
            .order_by(ProviderConfig.priority.asc())
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def get_by_name(self, name: str) -> ProviderConfig | None:
        statement = select(ProviderConfig).where(ProviderConfig.name == name)
        result = await self._session.execute(statement)
        return result.scalars().first()

    async def create(self, config: ProviderConfig) -> ProviderConfig:
        self._session.add(config)
        await self._session.commit()
        await self._session.refresh(config)
        return config

    async def update(self, config: ProviderConfig, values: dict) -> ProviderConfig:
        for key, value in values.items():
            setattr(config, key, value)
        await self._session.commit()
        await self._session.refresh(config)
        return config
