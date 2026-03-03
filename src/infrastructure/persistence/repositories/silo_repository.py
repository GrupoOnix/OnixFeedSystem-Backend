from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.silo import Silo
from domain.repositories import ISiloRepository
from domain.value_objects import SiloId, SiloName, UserId
from infrastructure.persistence.models.doser_model import DoserModel
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel
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
            existing.food_id = silo.food_id.value if silo.food_id else None
            existing.is_assigned = silo.is_assigned
            existing.user_id = silo.user_id.value if silo.user_id else existing.user_id
            existing.created_at = silo._created_at
        else:
            silo_model = SiloModel.from_domain(silo)
            self.session.add(silo_model)

        await self.session.flush()

    async def find_by_id(self, silo_id: SiloId, user_id: UserId) -> Optional[Silo]:
        result = await self.session.execute(
            select(SiloModel).where(
                SiloModel.id == silo_id.value,
                SiloModel.user_id == user_id.value,
            )
        )
        silo_model = result.scalar_one_or_none()
        return silo_model.to_domain() if silo_model else None

    async def find_by_name(self, name: SiloName, user_id: UserId) -> Optional[Silo]:
        result = await self.session.execute(
            select(SiloModel).where(
                SiloModel.name == str(name),
                SiloModel.user_id == user_id.value,
            )
        )
        silo_model = result.scalar_one_or_none()
        return silo_model.to_domain() if silo_model else None

    async def get_all(self, user_id: UserId) -> List[Silo]:
        result = await self.session.execute(select(SiloModel).where(SiloModel.user_id == user_id.value))
        silo_models = result.scalars().all()
        return [model.to_domain() for model in silo_models]

    async def delete(self, silo_id: SiloId, user_id: UserId) -> None:
        result = await self.session.execute(
            select(SiloModel).where(
                SiloModel.id == silo_id.value,
                SiloModel.user_id == user_id.value,
            )
        )
        silo_model = result.scalar_one_or_none()
        if silo_model:
            await self.session.delete(silo_model)
            await self.session.flush()

    async def find_all_with_line_info(
        self, user_id: UserId, is_assigned: Optional[bool] = None
    ) -> List[Tuple[Silo, Optional[str], Optional[str]]]:
        """
        Obtiene todos los silos con información de la línea asignada.

        Returns:
            List[Tuple[Silo, line_id, line_name]]: Lista de tuplas con el silo
            y opcionalmente el ID y nombre de la línea a la que está asignado.
        """
        query = (
            select(SiloModel, DoserModel.line_id, FeedingLineModel.name)
            .outerjoin(DoserModel, DoserModel.silo_id == SiloModel.id)
            .outerjoin(FeedingLineModel, FeedingLineModel.id == DoserModel.line_id)
            .where(SiloModel.user_id == user_id.value)
        )

        if is_assigned is not None:
            query = query.where(SiloModel.is_assigned == is_assigned)

        result = await self.session.execute(query)
        rows = result.all()

        return [
            (
                row.SiloModel.to_domain(),
                str(row.line_id) if row.line_id else None,
                row.name if row.name else None,
            )
            for row in rows
        ]

    async def find_by_id_with_line_info(
        self, silo_id: SiloId, user_id: UserId
    ) -> Optional[Tuple[Silo, Optional[str], Optional[str]]]:
        """
        Obtiene un silo por ID con información de la línea asignada.

        Returns:
            Optional[Tuple[Silo, line_id, line_name]]: Tupla con el silo
            y opcionalmente el ID y nombre de la línea a la que está asignado.
        """
        query = (
            select(SiloModel, DoserModel.line_id, FeedingLineModel.name)
            .outerjoin(DoserModel, DoserModel.silo_id == SiloModel.id)
            .outerjoin(FeedingLineModel, FeedingLineModel.id == DoserModel.line_id)
            .where(
                SiloModel.id == silo_id.value,
                SiloModel.user_id == user_id.value,
            )
        )

        result = await self.session.execute(query)
        row = result.first()

        if not row:
            return None

        return (
            row.SiloModel.to_domain(),
            str(row.line_id) if row.line_id else None,
            row.name if row.name else None,
        )
