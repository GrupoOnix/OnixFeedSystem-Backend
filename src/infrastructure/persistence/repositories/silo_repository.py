from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.aggregates.silo import Silo
from domain.repositories import ISiloRepository
from domain.value_objects import SiloId, SiloName
from infrastructure.persistence.models.doser_model import DoserModel
from infrastructure.persistence.models.doser_silo_model import DoserSiloModel
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel
from infrastructure.persistence.models.silo_model import SiloModel
from infrastructure.persistence.repositories.silo_inventory_repository import (
    SiloInventoryRepository,
)


class SiloRepository(ISiloRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, silo: Silo) -> None:
        existing = await self.session.get(SiloModel, silo.id.value)

        if existing:
            existing.name = str(silo.name)
            existing.capacity_mg = silo.capacity.as_miligrams
            existing.warning_threshold_percentage = silo.warning_threshold_percentage
            existing.critical_threshold_percentage = silo.critical_threshold_percentage
            existing.created_at = silo._created_at
        else:
            silo_model = SiloModel.from_domain(silo)
            self.session.add(silo_model)

        await self.session.flush()

    async def find_by_id(self, silo_id: SiloId) -> Optional[Silo]:
        silo_model = await self.session.get(SiloModel, silo_id.value)
        if not silo_model:
            return None
        silo = silo_model.to_domain()
        silo._is_assigned = await self._has_doser_links(silo_id)
        await self._load_inventory(silo)
        return silo

    async def find_by_name(self, name: SiloName) -> Optional[Silo]:
        result = await self.session.execute(
            select(SiloModel).where(col(SiloModel.name) == str(name))
        )
        silo_model = result.scalar_one_or_none()
        if not silo_model:
            return None
        silo = silo_model.to_domain()
        silo._is_assigned = await self._has_doser_links(SiloId(silo_model.id))
        await self._load_inventory(silo)
        return silo

    async def get_all(self) -> List[Silo]:
        result = await self.session.execute(select(SiloModel))
        silo_models = result.scalars().all()
        silos = []
        for model in silo_models:
            silo = model.to_domain()
            silo._is_assigned = await self._has_doser_links(SiloId(model.id))
            await self._load_inventory(silo)
            silos.append(silo)
        return silos

    async def delete(self, silo_id: SiloId) -> None:
        silo_model = await self.session.get(SiloModel, silo_id.value)
        if silo_model:
            await self.session.delete(silo_model)
            await self.session.flush()

    async def find_all_with_line_info(
        self, is_assigned: Optional[bool] = None
    ) -> List[Tuple[Silo, List[str], List[str]]]:
        """
        Obtiene todos los silos con información de la línea asignada.

        Returns:
            Lista de tuplas con el silo y las líneas a las que está asignado.
        """
        query = (
            select(SiloModel, col(DoserModel.line_id), col(FeedingLineModel.name))
            .outerjoin(
                DoserSiloModel,
                col(DoserSiloModel.silo_id) == col(SiloModel.id),
            )
            .outerjoin(
                DoserModel,
                col(DoserModel.id) == col(DoserSiloModel.doser_id),
            )
            .outerjoin(
                FeedingLineModel,
                col(FeedingLineModel.id) == col(DoserModel.line_id),
            )
        )

        if is_assigned is not None:
            if is_assigned:
                query = query.where(col(DoserSiloModel.doser_id).is_not(None))
            else:
                query = query.where(col(DoserSiloModel.doser_id).is_(None))

        result = await self.session.execute(query)
        rows = result.all()

        grouped: dict[object, tuple[Silo, set[str], set[str]]] = {}
        for row in rows:
            silo = row.SiloModel.to_domain()
            silo._is_assigned = row.line_id is not None
            await self._load_inventory(silo)
            entry = grouped.setdefault(row.SiloModel.id, (silo, set(), set()))
            if row.line_id:
                entry[1].add(str(row.line_id))
            if row.name:
                entry[2].add(row.name)

        return [(silo, sorted(line_ids), sorted(line_names)) for silo, line_ids, line_names in grouped.values()]

    async def find_by_id_with_line_info(
        self, silo_id: SiloId
    ) -> Optional[Tuple[Silo, List[str], List[str]]]:
        """
        Obtiene un silo por ID con información de la línea asignada.

        Returns:
            Tupla con el silo y las líneas a las que está asignado.
        """
        query = (
            select(SiloModel, col(DoserModel.line_id), col(FeedingLineModel.name))
            .outerjoin(
                DoserSiloModel,
                col(DoserSiloModel.silo_id) == col(SiloModel.id),
            )
            .outerjoin(
                DoserModel,
                col(DoserModel.id) == col(DoserSiloModel.doser_id),
            )
            .outerjoin(
                FeedingLineModel,
                col(FeedingLineModel.id) == col(DoserModel.line_id),
            )
            .where(col(SiloModel.id) == silo_id.value)
        )

        result = await self.session.execute(query)
        rows = result.all()

        if not rows:
            return None

        silo = rows[0].SiloModel.to_domain()
        line_ids = sorted({str(row.line_id) for row in rows if row.line_id})
        line_names = sorted({row.name for row in rows if row.name})
        silo._is_assigned = bool(line_ids)
        await self._load_inventory(silo)

        return (
            silo,
            line_ids,
            line_names,
        )

    async def _has_doser_links(self, silo_id: SiloId) -> bool:
        result = await self.session.execute(
            select(func.count(col(DoserSiloModel.doser_id))).where(
                col(DoserSiloModel.silo_id) == silo_id.value
            )
        )
        return result.scalar_one() > 0

    async def _load_inventory(self, silo: Silo) -> None:
        inventory_repo = SiloInventoryRepository(self.session)
        summary = await inventory_repo.get_summary(silo.id.value)
        batches = await inventory_repo.list_batches(
            silo.id.value,
            statuses=[],
            limit=10000,
        )
        active_batches = [batch for batch in batches if batch.status.value == "ACTIVE"]
        from domain.value_objects import Weight

        silo.load_inventory(
            total_stock=Weight.from_miligrams(summary.total_stock_mg),
            reserved_stock=Weight.from_miligrams(summary.reserved_stock_mg),
            active_batches=active_batches,
        )
