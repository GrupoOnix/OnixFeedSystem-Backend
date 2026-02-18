from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.feeding_event import FeedingEvent, FeedingEventType
from domain.repositories import IFeedingEventRepository
from infrastructure.persistence.models.feeding_event_model import FeedingEventModel


class FeedingEventRepository(IFeedingEventRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, event: FeedingEvent) -> None:
        model = FeedingEventModel.from_domain(event)
        self.session.add(model)
        await self.session.flush()

    async def save_many(self, events: List[FeedingEvent]) -> None:
        models = [FeedingEventModel.from_domain(event) for event in events]
        self.session.add_all(models)
        await self.session.flush()

    async def find_by_session(self, session_id: str) -> List[FeedingEvent]:
        query = (
            select(FeedingEventModel)
            .where(FeedingEventModel.feeding_session_id == session_id)
            .order_by(FeedingEventModel.timestamp.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def find_by_type(self, session_id: str, event_type: FeedingEventType) -> List[FeedingEvent]:
        query = (
            select(FeedingEventModel)
            .where(
                and_(
                    FeedingEventModel.feeding_session_id == session_id,
                    FeedingEventModel.event_type == event_type.value
                )
            )
            .order_by(FeedingEventModel.timestamp.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]
