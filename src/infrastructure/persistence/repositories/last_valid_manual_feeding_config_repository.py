from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from infrastructure.persistence.models.last_valid_manual_feeding_config_model import (
    LastValidManualFeedingConfigModel,
)


class LastValidManualFeedingConfigRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> List[LastValidManualFeedingConfigModel]:
        result = await self.session.execute(select(LastValidManualFeedingConfigModel))
        return list(result.scalars().all())

    async def find_by_line_id(self, line_id: UUID) -> Optional[LastValidManualFeedingConfigModel]:
        result = await self.session.execute(
            select(LastValidManualFeedingConfigModel).where(
                col(LastValidManualFeedingConfigModel.line_id) == line_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert_by_line_id(
        self,
        *,
        line_id: UUID,
        target_silo_id: UUID,
        target_cage_id: UUID,
        target_amount_kg: float,
        dosing_rate_kg_per_min: float,
        dosing_unit: str,
        blower_power_percentage: float,
        updated_by: Optional[str] = None,
    ) -> LastValidManualFeedingConfigModel:
        existing = await self.find_by_line_id(line_id)

        if existing:
            if _matches(
                existing,
                target_silo_id=target_silo_id,
                target_cage_id=target_cage_id,
                target_amount_kg=target_amount_kg,
                dosing_rate_kg_per_min=dosing_rate_kg_per_min,
                dosing_unit=dosing_unit,
                blower_power_percentage=blower_power_percentage,
                updated_by=updated_by,
            ):
                return existing

            existing.target_silo_id = target_silo_id
            existing.target_cage_id = target_cage_id
            existing.target_amount_kg = target_amount_kg
            existing.dosing_rate_kg_per_min = dosing_rate_kg_per_min
            existing.dosing_unit = dosing_unit
            existing.blower_power_percentage = blower_power_percentage
            existing.updated_by = updated_by
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            return existing

        model = LastValidManualFeedingConfigModel(
            line_id=line_id,
            target_silo_id=target_silo_id,
            target_cage_id=target_cage_id,
            target_amount_kg=target_amount_kg,
            dosing_rate_kg_per_min=dosing_rate_kg_per_min,
            dosing_unit=dosing_unit,
            blower_power_percentage=blower_power_percentage,
            updated_by=updated_by,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model


def _matches(
    model: LastValidManualFeedingConfigModel,
    *,
    target_silo_id: UUID,
    target_cage_id: UUID,
    target_amount_kg: float,
    dosing_rate_kg_per_min: float,
    dosing_unit: str,
    blower_power_percentage: float,
    updated_by: Optional[str],
) -> bool:
    return (
        model.target_silo_id == target_silo_id
        and model.target_cage_id == target_cage_id
        and model.target_amount_kg == target_amount_kg
        and model.dosing_rate_kg_per_min == dosing_rate_kg_per_min
        and model.dosing_unit == dosing_unit
        and model.blower_power_percentage == blower_power_percentage
        and model.updated_by == updated_by
    )
