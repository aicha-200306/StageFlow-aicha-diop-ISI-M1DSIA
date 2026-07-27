from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.offer import Application, ApplicationStatus

class ApplicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, application: Application) -> Application:
        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def get(self, application_id: int) -> Application | None:
        return await self.db.get(Application, application_id)

    async def get_active_for_student_and_offer(self, offer_id: int, student_id: int) -> Application | None:
        result = await self.db.execute(
            select(Application).where(
                Application.offer_id == offer_id,
                Application.student_id == student_id,
                Application.status.in_([ApplicationStatus.pending, ApplicationStatus.accepted]),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_student(self, student_id: int) -> list[Application]:
        result = await self.db.execute(select(Application).where(Application.student_id == student_id))
        return list(result.scalars().all())

    async def update_status(self, application: Application, new_status: ApplicationStatus) -> Application:
        application.status = new_status
        await self.db.commit()
        await self.db.refresh(application)
        return application