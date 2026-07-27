import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_cannot_submit_incomplete_offer(client: AsyncClient, company_token: str):
    create_response = await client.post(
        "/offers",
        json={"title": "Stage incomplet"},  # mission et skills manquants
        headers={"Authorization": f"Bearer {company_token}"},
    )
    assert create_response.status_code == 201
    offer_id = create_response.json()["id"]

    submit_response = await client.patch(
        f"/offers/{offer_id}/submit",
        headers={"Authorization": f"Bearer {company_token}"},
    )
    assert submit_response.status_code == 400