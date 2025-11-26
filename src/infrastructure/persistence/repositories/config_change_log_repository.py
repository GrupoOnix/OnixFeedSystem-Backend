from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories import IConfigChangeLogRepository
from domain.value_objects import CageId
from domain.value_objects.config_change_log_entry import ConfigChangeLogEntry
from infrastructure.persistence.models.config_change_log_model import ConfigChangeLogModel


class ConfigChangeLogRepository(IConfigChangeLogRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_batch(self, log_entries: List[ConfigChangeLogEntry]) -> None:
        """
        Guarda múltiples registros de cambios en una sola transacción.
        Útil cuando se actualizan varios campos a la vez.
        """
        for entry in log_entries:
            log_model = ConfigChangeLogModel.from_domain(entry)
            self.session.add(log_model)
        await self.session.flush()

    async def list_by_cage(self, cage_id: CageId, limit: int = 50, offset: int = 0) -> List[ConfigChangeLogEntry]:
        """Lista registros de cambios de configuración de una jaula, ordenados por fecha DESC."""
        result = await self.session.execute(
            select(ConfigChangeLogModel)
            .where(ConfigChangeLogModel.cage_id == cage_id.value)
            .order_by(ConfigChangeLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def count_by_cage(self, cage_id: CageId) -> int:
        """Cuenta total de registros de cambios de configuración de una jaula."""
        result = await self.session.execute(
            select(func.count(ConfigChangeLogModel.change_id))
            .where(ConfigChangeLogModel.cage_id == cage_id.value)
        )
        return result.scalar() or 0
