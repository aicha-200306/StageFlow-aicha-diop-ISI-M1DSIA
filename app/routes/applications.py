from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies.permissions import require_role
from app.repositories.application_repository import ApplicationRepository
from app.models.offer import ApplicationStatus
from app.schemas.offer import ApplicationOut, ApplicationDecisionRequest

router = APIRouter(prefix="/applications", tags=["applications"])

@router.get("/me")
async def list_my_applications(
    payload: dict = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    repo = ApplicationRepository(db)
    return await repo.list_for_student(int(payload["sub"]))


@router.patch("/{application_id}/decision", response_model=ApplicationOut)
async def decide_application(
    application_id: int,
    decision: ApplicationDecisionRequest,
    payload: dict = Depends(require_role("program_manager")),
    db: AsyncSession = Depends(get_db),
):
    repo = ApplicationRepository(db)
    application = await repo.get(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    if decision.decision == "accept":
        new_status = ApplicationStatus.accepted
    elif decision.decision == "reject":
        new_status = ApplicationStatus.rejected
    else:
        raise HTTPException(status_code=400, detail="Décision invalide")
    return await repo.update_status(application, new_status)


@router.delete("/{application_id}", status_code=204)
async def withdraw_application(
    application_id: int,
    payload: dict = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    repo = ApplicationRepository(db)
    application = await repo.get(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    if application.student_id != int(payload["sub"]):
        raise HTTPException(status_code=403, detail="Non autorisé")
    if application.status == ApplicationStatus.accepted:
        raise HTTPException(status_code=400, detail="Impossible de retirer une candidature acceptée")
    await repo.update_status(application, ApplicationStatus.withdrawn)