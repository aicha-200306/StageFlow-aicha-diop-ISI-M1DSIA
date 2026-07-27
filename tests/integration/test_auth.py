import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, company_user):
    response = await client.post(
        "/auth/login",
        data={"username": "company1@test.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, company_user):
    response = await client.post(
        "/auth/login",
        data={"username": "company1@test.com", "password": "mauvais_mot_de_passe"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_without_token_returns_401(client: AsyncClient, other_company_offer_id: int):
    response = await client.get(f"/offers/{other_company_offer_id}/applications")
    assert response.status_code == 401