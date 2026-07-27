import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_nominal_flow(
    client: AsyncClient,
    company_token: str,
    student_token: str,
    program_manager_token: str,
):
    create_response = await client.post(
        "/offers",
        json={"title": "Stage Data", "mission": "Analyser des données", "skills": "Python"},
        headers={"Authorization": f"Bearer {company_token}"},
    )
    assert create_response.status_code == 201
    offer_id = create_response.json()["id"]

    submit_response = await client.patch(
        f"/offers/{offer_id}/submit",
        headers={"Authorization": f"Bearer {company_token}"},
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "submitted"

    review_response = await client.patch(
        f"/offers/{offer_id}/review",
        json={"decision": "publish"},
        headers={"Authorization": f"Bearer {program_manager_token}"},
    )
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "published"

    apply_response = await client.post(
        f"/offers/{offer_id}/applications",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert apply_response.status_code == 201
    application_id = apply_response.json()["id"]
    assert apply_response.json()["status"] == "pending"

    decision_response = await client.patch(
        f"/applications/{application_id}/decision",
        json={"decision": "accept"},
        headers={"Authorization": f"Bearer {program_manager_token}"},
    )
    assert decision_response.status_code == 200
    assert decision_response.json()["status"] == "accepted"