from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.entities.cage_feeding import CageFeeding, CageFeedingMode, CageFeedingStatus
from domain.repositories import ICageFeedingRepository
from infrastructure.persistence.models.cage_feeding_model import CageFeedingModel


class CageFeedingRepository(ICageFeedingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, cage_feeding: CageFeeding) -> None:
        model = CageFeedingModel.from_domain(cage_feeding)
        await self.session.merge(model)
        await self.session.flush()

    async def find_by_id(self, id: str) -> Optional[CageFeeding]:
        query = select(CageFeedingModel).where(col(CageFeedingModel.id) == id)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def find_by_session(self, session_id: str) -> List[CageFeeding]:
        query = (
            select(CageFeedingModel)
            .where(col(CageFeedingModel.feeding_session_id) == session_id)
            .order_by(col(CageFeedingModel.execution_order))
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def find_current_by_session(self, session_id: str) -> Optional[CageFeeding]:
        query = select(CageFeedingModel).where(
            and_(
                col(CageFeedingModel.feeding_session_id) == session_id,
                col(CageFeedingModel.status) == CageFeedingStatus.IN_PROGRESS.value,
            )
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def mark_visit_started(self, id: str) -> CageFeeding:
        model = await self._find_model_for_update(id)
        cage_feeding = model.to_domain()
        if cage_feeding.status == CageFeedingStatus.PENDING:
            cage_feeding.start()
            model.status = cage_feeding.status.value
            await self.session.flush()
        return model.to_domain()

    async def record_visit_progress(
        self,
        id: str,
        dispensed_kg: float,
        completed_visit: bool,
    ) -> CageFeeding:
        model = await self._find_model_for_update(id)
        cage_feeding = model.to_domain()
        if dispensed_kg > 0:
            cage_feeding.add_dispensed_amount(dispensed_kg)
        if completed_visit:
            if cage_feeding.status == CageFeedingStatus.PENDING:
                cage_feeding.start()
            if cage_feeding.status == CageFeedingStatus.IN_PROGRESS:
                cage_feeding.increment_completed_visits()
                if cage_feeding.completed_visits >= cage_feeding.programmed_visits:
                    cage_feeding.complete()

        model.dispensed_kg = cage_feeding.dispensed_kg
        model.completed_visits = cage_feeding.completed_visits
        model.status = cage_feeding.status.value
        await self.session.flush()
        return model.to_domain()

    async def update_rate(self, id: str, rate_kg_per_min: float) -> CageFeeding:
        model = await self._find_model_for_update(id)
        cage_feeding = model.to_domain()
        cage_feeding.set_rate(rate_kg_per_min)
        model.rate_kg_per_min = cage_feeding.rate_kg_per_min
        await self.session.flush()
        return model.to_domain()

    async def update_programmed_kg(self, id: str, programmed_kg: float) -> CageFeeding:
        model = await self._find_model_for_update(id)
        cage_feeding = model.to_domain()
        cage_feeding.set_programmed_kg(programmed_kg)
        model.programmed_kg = cage_feeding.programmed_kg
        await self.session.flush()
        return model.to_domain()

    async def update_amount_plan(
        self,
        id: str,
        programmed_kg: float,
        visit_quantities_kg: list[float],
    ) -> CageFeeding:
        model = await self._find_model_for_update(id)
        cage_feeding = model.to_domain()
        cage_feeding.set_amount_plan(programmed_kg, visit_quantities_kg)
        model.programmed_kg = cage_feeding.programmed_kg
        model.visit_quantities_kg = cage_feeding.visit_quantities_kg
        await self.session.flush()
        return model.to_domain()

    async def update_mode(self, id: str, mode: CageFeedingMode) -> CageFeeding:
        model = await self._find_model_for_update(id)
        cage_feeding = model.to_domain()
        cage_feeding.set_mode(mode)
        model.mode = cage_feeding.mode.value
        await self.session.flush()
        return model.to_domain()

    async def _find_model_for_update(self, id: str) -> CageFeedingModel:
        query = select(CageFeedingModel).where(col(CageFeedingModel.id) == id).with_for_update()
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            raise ValueError(f"Alimentación de jaula {id} no encontrada")
        return model

    async def get_today_dispensed_by_cage(self, cage_id: str) -> float:
        """
        Calcula el total de alimento dispensado a una jaula en el día actual.

        Args:
            cage_id: ID de la jaula (string UUID)

        Returns:
            Total de kg dispensados hoy (desde las 00:00 UTC)
        """
        today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
        cage_uuid = UUID(cage_id)

        query = select(func.coalesce(func.sum(col(CageFeedingModel.dispensed_kg)), 0)).where(
            col(CageFeedingModel.cage_id) == cage_uuid,
            col(CageFeedingModel.created_at) >= today_start,
        )

        result = await self.session.execute(query)
        total = result.scalar_one()
        return float(total)

    async def get_today_dispensed_by_cages(self, cage_ids: List[str]) -> dict[str, float]:
        """
        Calcula el total de alimento dispensado para múltiples jaulas en el día actual.

        Args:
            cage_ids: Lista de IDs de jaulas (strings UUID)

        Returns:
            Diccionario con cage_id (string) como clave y kg dispensados como valor
        """
        if not cage_ids:
            return {}

        today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
        cage_uuid_list: List[UUID] = [UUID(cid) for cid in cage_ids]

        query = (
            select(
                col(CageFeedingModel.cage_id),
                func.coalesce(func.sum(col(CageFeedingModel.dispensed_kg)), 0).label("total_dispensed"),
            )
            .where(
                col(CageFeedingModel.cage_id).in_(cage_uuid_list),
                col(CageFeedingModel.created_at) >= today_start,
            )
            .group_by(col(CageFeedingModel.cage_id))
        )

        result = await self.session.execute(query)
        rows = result.all()

        # Construir diccionario con todos los cage_ids, defaulting a 0
        dispensed_map: dict[str, float] = {cid: 0.0 for cid in cage_ids}
        for row in rows:
            dispensed_map[str(row.cage_id)] = float(row.total_dispensed)

        return dispensed_map
