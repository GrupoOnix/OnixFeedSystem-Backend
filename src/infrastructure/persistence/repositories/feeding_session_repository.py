from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.entities.feeding_session import FeedingSession, SessionStatus
from domain.repositories import IFeedingSessionRepository
from domain.value_objects.identifiers import UserId
from infrastructure.persistence.models.feeding_session_model import FeedingSessionModel


class FeedingSessionRepository(IFeedingSessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, feeding_session: FeedingSession) -> None:
        model = FeedingSessionModel.from_domain(feeding_session)
        await self.session.merge(model)
        await self.session.flush()

    async def find_by_id(self, session_id: str, user_id: UserId) -> Optional[FeedingSession]:
        query = (
            select(FeedingSessionModel)
            .where(
                and_(
                    FeedingSessionModel.id == session_id,
                    FeedingSessionModel.user_id == user_id.value,
                )
            )
            .options(selectinload(FeedingSessionModel.cage_feedings), selectinload(FeedingSessionModel.events))
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def find_active_by_line(self, line_id: str, user_id: UserId) -> Optional[FeedingSession]:
        query = (
            select(FeedingSessionModel)
            .where(
                and_(
                    FeedingSessionModel.line_id == line_id,
                    FeedingSessionModel.user_id == user_id.value,
                    FeedingSessionModel.status.in_([SessionStatus.IN_PROGRESS.value, SessionStatus.PAUSED.value]),
                )
            )
            .options(selectinload(FeedingSessionModel.cage_feedings), selectinload(FeedingSessionModel.events))
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def find_today_by_line(self, line_id: str, user_id: UserId) -> Optional[FeedingSession]:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        query = (
            select(FeedingSessionModel)
            .where(
                and_(
                    FeedingSessionModel.line_id == line_id,
                    FeedingSessionModel.user_id == user_id.value,
                    FeedingSessionModel.actual_start >= today_start,
                )
            )
            .options(selectinload(FeedingSessionModel.cage_feedings), selectinload(FeedingSessionModel.events))
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def list_by_date_range(self, start: datetime, end: datetime, user_id: UserId) -> List[FeedingSession]:
        query = (
            select(FeedingSessionModel)
            .where(
                and_(
                    FeedingSessionModel.actual_start >= start,
                    FeedingSessionModel.actual_start <= end,
                    FeedingSessionModel.user_id == user_id.value,
                )
            )
            .options(selectinload(FeedingSessionModel.cage_feedings), selectinload(FeedingSessionModel.events))
            .order_by(FeedingSessionModel.actual_start.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def find_active_sessions(self, user_id: UserId, hours_back: int = 24) -> List[FeedingSession]:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        query = (
            select(FeedingSessionModel)
            .where(
                and_(
                    FeedingSessionModel.status.in_([SessionStatus.IN_PROGRESS.value, SessionStatus.PAUSED.value]),
                    FeedingSessionModel.user_id == user_id.value,
                    FeedingSessionModel.actual_start >= cutoff_time,
                )
            )
            .options(selectinload(FeedingSessionModel.cage_feedings), selectinload(FeedingSessionModel.events))
            .order_by(FeedingSessionModel.actual_start.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]
