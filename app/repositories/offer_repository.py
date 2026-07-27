from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.offer import Offer, OfferStatus

class OfferRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, offer: Offer) -> Offer:
        self.db.add(offer)
        await self.db.commit()
        await self.db.refresh(offer)
        return offer

    async def get(self, offer_id: int) -> Offer | None:
        result = await self.db.execute(
            select(Offer).options(selectinload(Offer.applications)).where(Offer.id == offer_id)
        )
        return result.scalar_one_or_none()

    async def list_published(self) -> list[Offer]:
        result = await self.db.execute(select(Offer).where(Offer.status == OfferStatus.published))
        return list(result.scalars().all())

    async def update_status(self, offer: Offer, new_status: OfferStatus) -> Offer:
        offer.status = new_status
        await self.db.commit()
        await self.db.refresh(offer)
        return offer