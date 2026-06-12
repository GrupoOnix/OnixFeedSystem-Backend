from datetime import datetime, timedelta
from typing import Any, List
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.dtos.feeding_rate_timeline import FeedingRateTimelineVisit
from domain.entities.feeding_event import FeedingEvent, FeedingEventType
from domain.repositories import IFeedingEventRepository
from infrastructure.persistence.models.feeding_event_model import FeedingEventModel
from infrastructure.persistence.models.feeding_session_model import FeedingSessionModel


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
            .where(col(FeedingEventModel.feeding_session_id) == session_id)
            .order_by(col(FeedingEventModel.timestamp).desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def find_by_type(self, session_id: str, event_type: FeedingEventType) -> List[FeedingEvent]:
        query = (
            select(FeedingEventModel)
            .where(
                and_(
                    col(FeedingEventModel.feeding_session_id) == session_id,
                    col(FeedingEventModel.event_type) == event_type.value
                )
            )
            .order_by(col(FeedingEventModel.timestamp).desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def list_rate_timeline_visits(
        self,
        start: datetime,
        end: datetime,
        line_id: str | None = None,
        cage_id: str | None = None,
        feeding_type: str | None = None,
    ) -> List[FeedingRateTimelineVisit]:
        lookback_start = start - timedelta(days=1)
        conditions: list[Any] = [
            col(FeedingEventModel.event_type) == FeedingEventType.VISIT_COMPLETED.value,
            col(FeedingEventModel.timestamp) >= lookback_start,
            col(FeedingEventModel.timestamp) <= end,
        ]

        if line_id:
            conditions.append(col(FeedingSessionModel.line_id) == UUID(line_id))
        if feeding_type:
            conditions.append(col(FeedingSessionModel.type) == feeding_type)

        query = (
            select(
                FeedingEventModel,
                col(FeedingSessionModel.id),
                col(FeedingSessionModel.type),
                col(FeedingSessionModel.line_id),
            )
            .join(
                FeedingSessionModel,
                col(FeedingEventModel.feeding_session_id) == col(FeedingSessionModel.id),
            )
            .where(and_(*conditions))
            .order_by(col(FeedingEventModel.timestamp).asc())
        )
        result = await self.session.execute(query)

        visits: list[FeedingRateTimelineVisit] = []
        for event, session_id, session_type, session_line_id in result.all():
            event_cage_id = event.data.get("cage_id") if event.data else None
            if not event_cage_id or (cage_id and event_cage_id != cage_id):
                continue

            duration_seconds = float(event.data.get("duration_seconds") or 0)
            dispensed_grams = float(event.data.get("dispensed_grams") or 0)
            if duration_seconds <= 0 or dispensed_grams <= 0:
                continue

            visits.append(
                FeedingRateTimelineVisit(
                    session_id=session_id,
                    feeding_type=session_type,
                    line_id=str(session_line_id),
                    cage_id=event_cage_id,
                    completed_at=event.timestamp,
                    duration_seconds=duration_seconds,
                    dispensed_kg=dispensed_grams / 1000,
                )
            )

        return visits
