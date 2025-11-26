from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories import IMortalityLogRepository
from domain.value_objects import CageId
from domain.value_objects.mortality_log_entry import MortalityLogEntry
from infrastructure.persistence.models.mortality_log_model import MortalityLogModel


class MortalityLogRepository(IMortalityLogRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, log_entry: MortalityLogEntry) -> None:
        """Guarda un registro de mortalidad."""
        log_model = MortalityLogModel.from_domain(log_entry)
        self.session.add(log_model)
        await self.session.flush()

    async def list_by_cage(self, cage_id: CageId, limit: int = 50, offset: int = 0) -> List[MortalityLogEntry]:
        """Lista registros de mortalidad de una jaula, ordenados por fecha DESC."""
        result = await self.session.execute(
            select(MortalityLogModel)
            .where(MortalityLogModel.cage_id == cage_id.value)
            .order_by(MortalityLogModel.mortality_date.desc(), MortalityLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def count_by_cage(self, cage_id: CageId) -> int:
        """Cuenta total de registros de mortalidad de una jaula."""
        result = await self.session.execute(
            select(func.count(MortalityLogModel.mortality_id))
            .where(MortalityLogModel.cage_id == cage_id.value)
        )
        return result.scalar() or 0

    async def get_total_mortality(self, cage_id: CageId) -> int:
        """
        Calcula la mortalidad acumulada total de una jaula.
        Suma todos los dead_fish_count del log.
        """
        result = await self.session.execute(
            select(func.coalesce(func.sum(MortalityLogModel.dead_fish_count), 0))
            .where(MortalityLogModel.cage_id == cage_id.value)
        )
        return result.scalar() or 0
