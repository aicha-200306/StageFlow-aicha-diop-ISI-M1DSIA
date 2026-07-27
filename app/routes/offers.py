from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies.permissions import require_role
from app.repositories.offer_repository import OfferRepository
from app.models.offer import Offer, OfferStatus
from app.schemas.offer import OfferCreate, OfferOut
from app.schemas.offer import OfferReviewDecision, ApplicationOut
from app.repositories.application_repository import ApplicationRepository
from app.models.offer import Application, ApplicationStatus

router = APIRouter(prefix="/offers", tags=["offers"])

@router.post("", response_model=OfferOut, status_code=201)
async def create_offer(
    data: OfferCreate,
    payload: dict = Depends(require_role("company")),
    db: AsyncSession = Depends(get_db),
):
    repo = OfferRepository(db)
    offer = Offer(**data.model_dump(), company_id=int(payload["sub"]), status=OfferStatus.draft)
    return await repo.create(offer)

@router.patch("/{offer_id}/submit", response_model=OfferOut)
async def submit_offer(
    offer_id: int,
    payload: dict = Depends(require_role("company")),
    db: AsyncSession = Depends(get_db),
):
    repo = OfferRepository(db)
    offer = await repo.get(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    if offer.company_id != int(payload["sub"]):
        raise HTTPException(status_code=403, detail="Non autorisé")
    if not (offer.title and offer.mission and offer.skills):
        raise HTTPException(status_code=400, detail="Offre incomplète")
    return await repo.update_status(offer, OfferStatus.submitted)

@router.get("/{offer_id}/applications")
async def list_applications(
    offer_id: int,
    payload: dict = Depends(require_role("company", "program_manager")),
    db: AsyncSession = Depends(get_db),
):
    repo = OfferRepository(db)
    offer = await repo.get(offer_id)
    if not offer or (payload["role"] == "company" and offer.company_id != int(payload["sub"])):
        raise HTTPException(status_code=404, detail="Offre introuvable")
    return offer.applications

@router.patch("/{offer_id}/review", response_model=OfferOut)
async def review_offer(
    offer_id: int,
    decision: OfferReviewDecision,
    payload: dict = Depends(require_role("program_manager")),
    db: AsyncSession = Depends(get_db),
):
    repo = OfferRepository(db)
    offer = await repo.get(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    if offer.status != OfferStatus.submitted:
        raise HTTPException(status_code=400, detail="Offre non soumise")
    if decision.decision == "publish":
        new_status = OfferStatus.published
    elif decision.decision == "reject":
        new_status = OfferStatus.rejected
    else:
        raise HTTPException(status_code=400, detail="Décision invalide")
    return await repo.update_status(offer, new_status)


@router.post("/{offer_id}/applications", response_model=ApplicationOut, status_code=201)
async def apply_to_offer(
    offer_id: int,
    payload: dict = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    offer_repo = OfferRepository(db)
    app_repo = ApplicationRepository(db)
    offer = await offer_repo.get(offer_id)
    if not offer or offer.status != OfferStatus.published:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    student_id = int(payload["sub"])
    existing = await app_repo.get_active_for_student_and_offer(offer_id, student_id)
    if existing:
        raise HTTPException(status_code=400, detail="Candidature déjà active pour cette offre")
    application = Application(offer_id=offer_id, student_id=student_id, status=ApplicationStatus.pending)
    return await app_repo.create(application)