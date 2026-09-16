"""
schemas/providers.py

Provider configuration and health API contracts.
"""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, HttpUrl


class ProviderConfigCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    endpoint: HttpUrl | None = None
    api_key: str | None = None
    priority: int = Field(default=100, ge=1)
    enabled: bool = Field(default=True)
    metadata: dict[str, object] = Field(default_factory=dict)


class ProviderConfigUpdateRequest(BaseModel):
    endpoint: HttpUrl | None = None
    api_key: str | None = None
    priority: int | None = Field(default=None, ge=1)
    enabled: bool | None = None
    metadata: dict[str, object] | None = None


class ProviderConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    endpoint: str | None = None
    api_key: str | None = None
    priority: int
    enabled: bool
    metadata: dict[str, object] = Field(
        validation_alias=AliasChoices("meta", "metadata"),
        serialization_alias="metadata",
    )


class ProviderHealthResponse(BaseModel):
    name: str
    available: bool
    detail: str | None = None
