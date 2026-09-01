"""Repositorio de planes diarios de alimentación programada."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from infrastructure.persistence.models.scheduled_feeding_plan_model import (
    ScheduledFeedingPlanModel,
)
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel


class ScheduledFeedingPlanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> List[ScheduledFeedingPlanModel]:
        result = await self.session.execute(
            select(ScheduledFeedingPlanModel).order_by(
                col(ScheduledFeedingPlanModel.start_time),
                col(ScheduledFeedingPlanModel.name),
            )
        )
        return list(result.scalars().all())

    async def list_for_owner(self, owner_id: UUID) -> List[ScheduledFeedingPlanModel]:
        result = await self.session.execute(
            select(ScheduledFeedingPlanModel)
            .where(col(ScheduledFeedingPlanModel.created_by_id) == owner_id)
            .order_by(col(ScheduledFeedingPlanModel.start_time), col(ScheduledFeedingPlanModel.name))
        )
        return list(result.scalars().all())

    async def find_by_id(self, plan_id: UUID) -> Optional[ScheduledFeedingPlanModel]:
        return await self.session.get(ScheduledFeedingPlanModel, plan_id)

    async def find_by_line(self, line_id: UUID) -> Optional[ScheduledFeedingPlanModel]:
        result = await self.session.execute(
            select(ScheduledFeedingPlanModel).where(col(ScheduledFeedingPlanModel.line_id) == line_id)
        )
        return result.scalars().first()

    async def lock_line_schedule(self, line_id: UUID) -> None:
        result = await self.session.execute(
            select(col(FeedingLineModel.id)).where(col(FeedingLineModel.id) == line_id).with_for_update()
        )
        if result.scalar_one_or_none() is None:
            raise ValueError("La línea seleccionada no existe")

    async def save(self, plan: ScheduledFeedingPlanModel) -> ScheduledFeedingPlanModel:
        plan.updated_at = datetime.now(timezone.utc)
        self.session.add(plan)
        await self.session.flush()
        await self.session.refresh(plan)
        return plan

    async def delete(self, plan: ScheduledFeedingPlanModel) -> None:
        await self.session.delete(plan)
        await self.session.flush()
