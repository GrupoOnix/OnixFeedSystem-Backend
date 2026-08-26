"""Repositorio de planes diarios de alimentación programada."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.persistence.models.scheduled_feeding_plan_model import (
    ScheduledFeedingPlanModel,
)


class ScheduledFeedingPlanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> list[ScheduledFeedingPlanModel]:
        result = await self.session.execute(
            select(ScheduledFeedingPlanModel).order_by(
                ScheduledFeedingPlanModel.start_time,
                ScheduledFeedingPlanModel.name,
            )
        )
        return list(result.scalars().all())

    async def find_by_id(self, plan_id: UUID) -> Optional[ScheduledFeedingPlanModel]:
        return await self.session.get(ScheduledFeedingPlanModel, plan_id)

    async def save(self, plan: ScheduledFeedingPlanModel) -> ScheduledFeedingPlanModel:
        plan.updated_at = datetime.now(timezone.utc)
        self.session.add(plan)
        await self.session.flush()
        await self.session.refresh(plan)
        return plan

    async def delete(self, plan: ScheduledFeedingPlanModel) -> None:
        await self.session.delete(plan)
        await self.session.flush()
