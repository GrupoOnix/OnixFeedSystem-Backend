from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, cast

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col

from domain.entities.feeding_session import FeedingSession, SessionStatus
from domain.repositories import IFeedingSessionRepository
from infrastructure.persistence.models.feeding_session_model import FeedingSessionModel


_cage_feedings_rel = cast(Any, FeedingSessionModel.cage_feedings)
_events_rel = cast(Any, FeedingSessionModel.events)


class FeedingSessionRepository(IFeedingSessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, feeding_session: FeedingSession) -> None:
        model = FeedingSessionModel.from_domain(feeding_session)
        await self.session.merge(model)
        await self.session.flush()

    async def find_by_id(self, session_id: str) -> Optional[FeedingSession]:
        query = (
            select(FeedingSessionModel)
            .where(col(FeedingSessionModel.id) == session_id)
            .options(
                selectinload(_cage_feedings_rel),
                selectinload(_events_rel)
            )
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def find_active_by_line(self, line_id: str) -> Optional[FeedingSession]:
        query = (
            select(FeedingSessionModel)
            .where(
                and_(
                    col(FeedingSessionModel.line_id) == line_id,
                    col(FeedingSessionModel.status).in_([
                        SessionStatus.IN_PROGRESS.value,
                        SessionStatus.PAUSED.value
                    ])
                )
            )
            .options(
                selectinload(_cage_feedings_rel),
                selectinload(_events_rel)
            )
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def find_today_by_line(self, line_id: str) -> Optional[FeedingSession]:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        query = (
            select(FeedingSessionModel)
            .where(
                and_(
                    col(FeedingSessionModel.line_id) == line_id,
                    col(FeedingSessionModel.actual_start) >= today_start
                )
            )
            .options(
                selectinload(_cage_feedings_rel),
                selectinload(_events_rel)
            )
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def list_by_date_range(self, start: datetime, end: datetime) -> List[FeedingSession]:
        query = (
            select(FeedingSessionModel)
            .where(
                and_(
                    col(FeedingSessionModel.actual_start) >= start,
                    col(FeedingSessionModel.actual_start) <= end
                )
            )
            .options(
                selectinload(_cage_feedings_rel),
                selectinload(_events_rel)
            )
            .order_by(col(FeedingSessionModel.actual_start).desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def find_active_sessions(self, hours_back: int = 24) -> List[FeedingSession]:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        query = (
            select(FeedingSessionModel)
            .where(
                and_(
                    col(FeedingSessionModel.status).in_([
                        SessionStatus.IN_PROGRESS.value,
                        SessionStatus.PAUSED.value
                    ]),
                    col(FeedingSessionModel.actual_start) >= cutoff_time
                )
            )
            .options(
                selectinload(_cage_feedings_rel),
                selectinload(_events_rel)
            )
            .order_by(col(FeedingSessionModel.actual_start).desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]
