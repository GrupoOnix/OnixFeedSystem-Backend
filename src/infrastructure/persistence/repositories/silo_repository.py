from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.silo import Silo
from domain.repositories import ISiloRepository
from domain.value_objects import SiloId, SiloName
from infrastructure.persistence.models.silo_model import SiloModel


class SiloRepository(ISiloRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, silo: Silo) -> None:
        existing = await self.session.get(SiloModel, silo.id.value)

        if existing:
            existing.name = str(silo.name)
            existing.capacity_mg = silo.capacity.as_miligrams
            existing.stock_level_mg = silo.stock_level.as_miligrams
            existing.is_assigned = silo.is_assigned
            existing.created_at = silo._created_at
        else:
            silo_model = SiloModel.from_domain(silo)
            self.session.add(silo_model)
        
        await self.session.flush()

    async def find_by_id(self, silo_id: SiloId) -> Optional[Silo]:
        silo_model = await self.session.get(SiloModel, silo_id.value)
        return silo_model.to_domain() if silo_model else None

    async def find_by_name(self, name: SiloName) -> Optional[Silo]:
        result = await self.session.execute(
            select(SiloModel).where(SiloModel.name == str(name))
        )
        silo_model = result.scalar_one_or_none()
        return silo_model.to_domain() if silo_model else None

    async def get_all(self) -> List[Silo]:
        result = await self.session.execute(select(SiloModel))
        silo_models = result.scalars().all()
        return [model.to_domain() for model in silo_models]

    async def delete(self, silo_id: SiloId) -> None:
        silo_model = await self.session.get(SiloModel, silo_id.value)
        if silo_model:
            await self.session.delete(silo_model)
            await self.session.flush()
