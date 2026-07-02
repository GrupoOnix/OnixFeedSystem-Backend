from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.enums import ActivityLogCategory, ActivityLogEventType
from domain.repositories import ICageActivityLogRepository
from domain.value_objects import CageId
from domain.value_objects.activity_log_entry import ActivityLogEntry
from infrastructure.persistence.models.activity_log_model import ActivityLogModel


class ActivityLogRepository(ICageActivityLogRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, entry: ActivityLogEntry) -> None:
        """Guarda un registro de actividad."""
        model = ActivityLogModel.from_domain(entry)
        self.session.add(model)
        await self.session.flush()

    async def list_by_cage(
        self,
        cage_id: CageId,
        event_type: Optional[List[ActivityLogEventType]] = None,
        category: Optional[List[ActivityLogCategory]] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ActivityLogEntry]:
        """Lista registros de actividad de una jaula, ordenados por event_at DESC."""
        query = select(ActivityLogModel).where(col(ActivityLogModel.cage_id) == cage_id.value)

        if event_type:
            query = query.where(col(ActivityLogModel.event_type).in_([e.value for e in event_type]))
        if category:
            query = query.where(col(ActivityLogModel.category).in_([c.value for c in category]))
        if from_date:
            query = query.where(col(ActivityLogModel.event_at) >= from_date)
        if to_date:
            query = query.where(col(ActivityLogModel.event_at) <= to_date)

        query = query.order_by(col(ActivityLogModel.event_at).desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [model.to_domain() for model in result.scalars().all()]

    async def count_by_cage(
        self,
        cage_id: CageId,
        event_type: Optional[List[ActivityLogEventType]] = None,
        category: Optional[List[ActivityLogCategory]] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> int:
        """Cuenta registros de actividad de una jaula con filtros opcionales."""
        query = select(func.count(col(ActivityLogModel.log_id))).where(col(ActivityLogModel.cage_id) == cage_id.value)

        if event_type:
            query = query.where(col(ActivityLogModel.event_type).in_([e.value for e in event_type]))
        if category:
            query = query.where(col(ActivityLogModel.category).in_([c.value for c in category]))
        if from_date:
            query = query.where(col(ActivityLogModel.event_at) >= from_date)
        if to_date:
            query = query.where(col(ActivityLogModel.event_at) <= to_date)

        result = await self.session.execute(query)
        return result.scalar() or 0
