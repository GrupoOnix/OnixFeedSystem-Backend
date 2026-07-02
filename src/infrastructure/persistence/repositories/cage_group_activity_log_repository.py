from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.repositories import ICageGroupActivityLogRepository
from domain.value_objects import CageGroupId
from domain.value_objects.cage_group_activity_log_entry import CageGroupActivityLogEntry
from infrastructure.persistence.models.cage_group_activity_log_model import (
    CageGroupActivityLogModel,
)


class CageGroupActivityLogRepository(ICageGroupActivityLogRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, entry: CageGroupActivityLogEntry) -> None:
        """Guarda un registro de actividad de grupo."""
        model = CageGroupActivityLogModel.from_domain(entry)
        self.session.add(model)
        await self.session.flush()

    async def list_by_cage_group(
        self,
        cage_group_id: CageGroupId,
        limit: int = 20,
        offset: int = 0,
    ) -> List[CageGroupActivityLogEntry]:
        """Lista registros de actividad de un grupo, ordenados por event_at DESC."""
        query = (
            select(CageGroupActivityLogModel)
            .where(col(CageGroupActivityLogModel.cage_group_id) == cage_group_id.value)
            .order_by(col(CageGroupActivityLogModel.event_at).desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return [model.to_domain() for model in result.scalars().all()]

    async def count_by_cage_group(
        self,
        cage_group_id: CageGroupId,
    ) -> int:
        """Cuenta registros de actividad de un grupo."""
        query = select(func.count(col(CageGroupActivityLogModel.log_id))).where(
            col(CageGroupActivityLogModel.cage_group_id) == cage_group_id.value
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
