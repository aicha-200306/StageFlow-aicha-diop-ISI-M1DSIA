import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rate_limit_returns_429(client: AsyncClient):
    responses = []
    for _ in range(61):
        response = await client.get("/health")
        responses.append(response.status_code)
    assert 429 in responses