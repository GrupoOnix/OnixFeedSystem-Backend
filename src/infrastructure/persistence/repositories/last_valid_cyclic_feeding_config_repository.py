from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.persistence.models.last_valid_cyclic_feeding_config_model import (
    LastValidCyclicFeedingConfigModel,
)


class LastValidCyclicFeedingConfigRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> List[LastValidCyclicFeedingConfigModel]:
        result = await self.session.execute(select(LastValidCyclicFeedingConfigModel))
        return list(result.scalars().all())

    async def find_by_line_id(self, line_id: UUID) -> Optional[LastValidCyclicFeedingConfigModel]:
        result = await self.session.execute(
            select(LastValidCyclicFeedingConfigModel).where(LastValidCyclicFeedingConfigModel.line_id == line_id)
        )
        return result.scalar_one_or_none()

    async def upsert_by_line_id(
        self,
        *,
        line_id: UUID,
        group_id: UUID,
        doser_id: UUID,
        visits: int,
        blower_power_percentage: float,
        cage_configs: List[Dict[str, Any]],
        updated_by: Optional[str] = None,
    ) -> LastValidCyclicFeedingConfigModel:
        existing = await self.find_by_line_id(line_id)

        if existing:
            if _matches(
                existing,
                group_id=group_id,
                doser_id=doser_id,
                visits=visits,
                blower_power_percentage=blower_power_percentage,
                cage_configs=cage_configs,
                updated_by=updated_by,
            ):
                return existing

            existing.group_id = group_id
            existing.doser_id = doser_id
            existing.visits = visits
            existing.blower_power_percentage = blower_power_percentage
            existing.cage_configs = cage_configs
            existing.updated_by = updated_by
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            return existing

        model = LastValidCyclicFeedingConfigModel(
            line_id=line_id,
            group_id=group_id,
            doser_id=doser_id,
            visits=visits,
            blower_power_percentage=blower_power_percentage,
            cage_configs=cage_configs,
            updated_by=updated_by,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model


def _matches(
    model: LastValidCyclicFeedingConfigModel,
    *,
    group_id: UUID,
    doser_id: UUID,
    visits: int,
    blower_power_percentage: float,
    cage_configs: List[Dict[str, Any]],
    updated_by: Optional[str],
) -> bool:
    return (
        model.group_id == group_id
        and model.doser_id == doser_id
        and model.visits == visits
        and model.blower_power_percentage == blower_power_percentage
        and model.cage_configs == cage_configs
        and model.updated_by == updated_by
    )
