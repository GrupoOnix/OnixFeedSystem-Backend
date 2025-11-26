from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories import IBiometryLogRepository
from domain.value_objects import CageId
from domain.value_objects.biometry_log_entry import BiometryLogEntry
from infrastructure.persistence.models.biometry_log_model import BiometryLogModel


class BiometryLogRepository(IBiometryLogRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, log_entry: BiometryLogEntry) -> None:
        """Guarda un registro de biometría."""
        log_model = BiometryLogModel.from_domain(log_entry)
        self.session.add(log_model)
        await self.session.flush()

    async def list_by_cage(self, cage_id: CageId, limit: int = 50, offset: int = 0) -> List[BiometryLogEntry]:
        """Lista registros de biometría de una jaula, ordenados por fecha DESC."""
        result = await self.session.execute(
            select(BiometryLogModel)
            .where(BiometryLogModel.cage_id == cage_id.value)
            .order_by(BiometryLogModel.sampling_date.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def count_by_cage(self, cage_id: CageId) -> int:
        """Cuenta total de registros de biometría de una jaula."""
        result = await self.session.execute(
            select(func.count(BiometryLogModel.biometry_id))
            .where(BiometryLogModel.cage_id == cage_id.value)
        )
        return result.scalar() or 0
