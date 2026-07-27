from pydantic import BaseModel, ConfigDict
from app.models.offer import OfferStatus
from app.models.offer import ApplicationStatus

class OfferCreate(BaseModel):
    title: str | None = None
    mission: str | None = None
    skills: str | None = None

class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str | None
    mission: str | None
    skills: str | None
    status: OfferStatus
    company_id: int

class OfferReviewDecision(BaseModel):
    decision: str  

class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    offer_id: int
    student_id: int
    status: ApplicationStatus

class ApplicationDecisionRequest(BaseModel):
    decision: str