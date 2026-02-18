from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.cage_feeding import CageFeeding, CageFeedingStatus
from domain.repositories import ICageFeedingRepository
from infrastructure.persistence.models.cage_feeding_model import CageFeedingModel


class CageFeedingRepository(ICageFeedingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, cage_feeding: CageFeeding) -> None:
        model = CageFeedingModel.from_domain(cage_feeding)
        await self.session.merge(model)
        await self.session.flush()

    async def find_by_id(self, id: str) -> Optional[CageFeeding]:
        query = select(CageFeedingModel).where(CageFeedingModel.id == id)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def find_by_session(self, session_id: str) -> List[CageFeeding]:
        query = (
            select(CageFeedingModel)
            .where(CageFeedingModel.feeding_session_id == session_id)
            .order_by(CageFeedingModel.execution_order)
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def find_current_by_session(self, session_id: str) -> Optional[CageFeeding]:
        query = (
            select(CageFeedingModel)
            .where(
                and_(
                    CageFeedingModel.feeding_session_id == session_id,
                    CageFeedingModel.status == CageFeedingStatus.IN_PROGRESS.value
                )
            )
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()
