import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_company_cannot_see_others_applications(
    client: AsyncClient,
    company_token: str,
    other_company_offer_id: int,
):
    response = await client.get(
        f"/offers/{other_company_offer_id}/applications",
        headers={"Authorization": f"Bearer {company_token}"},
    )
    # 404 : l'offre existe mais est masquée à une entreprise non propriétaire
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_company_can_see_own_applications(
    client: AsyncClient,
    company_token_2: str,
    other_company_offer_id: int,
):
    response = await client.get(
        f"/offers/{other_company_offer_id}/applications",
        headers={"Authorization": f"Bearer {company_token_2}"},
    )
    # Le vrai propriétaire doit pouvoir accéder normalement
    assert response.status_code == 200