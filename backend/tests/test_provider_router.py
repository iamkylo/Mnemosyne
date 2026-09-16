import pytest

from providers.router import ProviderRouter
from schemas.providers import ProviderConfigResponse


@pytest.mark.asyncio
async def test_provider_router_uses_local_hashing_provider() -> None:
    router = ProviderRouter(
        [
            ProviderConfigResponse(
                id=1,
                name="local",
                endpoint=None,
                api_key=None,
                priority=1,
                enabled=True,
                metadata={},
            )
        ]
    )

    embeddings = await router.embed(["persistent project memory"])

    assert len(embeddings) == 1
    assert len(embeddings[0]) == 384
