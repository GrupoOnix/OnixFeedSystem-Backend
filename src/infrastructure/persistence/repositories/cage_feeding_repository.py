from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.cage_feeding import CageFeeding, CageFeedingStatus
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
        query = select(CageFeedingModel).where(CageFeedingModel.id == id)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def find_by_session(self, session_id: str) -> List[CageFeeding]:
        query = (
            select(CageFeedingModel)
            .where(CageFeedingModel.feeding_session_id == session_id)
            .order_by(CageFeedingModel.execution_order)
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def find_current_by_session(self, session_id: str) -> Optional[CageFeeding]:
        query = select(CageFeedingModel).where(
            and_(
                CageFeedingModel.feeding_session_id == session_id,
                CageFeedingModel.status == CageFeedingStatus.IN_PROGRESS.value,
            )
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return model.to_domain()

    async def get_today_dispensed_by_cage(self, cage_id: str) -> float:
        """
        Calcula el total de alimento dispensado a una jaula en el día actual.

        Args:
            cage_id: ID de la jaula (string UUID)

        Returns:
            Total de kg dispensados hoy (desde las 00:00 UTC)
        """
        today_start = datetime.combine(date.today(), datetime.min.time())
        cage_uuid = UUID(cage_id)

        query = select(func.coalesce(func.sum(CageFeedingModel.dispensed_kg), 0)).where(
            CageFeedingModel.cage_id == cage_uuid,
            CageFeedingModel.created_at >= today_start,
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

        today_start = datetime.combine(date.today(), datetime.min.time())
        cage_uuid_list: List[UUID] = [UUID(cid) for cid in cage_ids]

        query = (
            select(
                CageFeedingModel.cage_id,
                func.coalesce(func.sum(CageFeedingModel.dispensed_kg), 0).label("total_dispensed"),
            )
            .where(
                CageFeedingModel.cage_id.in_(cage_uuid_list),
                CageFeedingModel.created_at >= today_start,
            )
            .group_by(CageFeedingModel.cage_id)
        )

        result = await self.session.execute(query)
        rows = result.all()

        # Construir diccionario con todos los cage_ids, defaulting a 0
        dispensed_map: dict[str, float] = {cid: 0.0 for cid in cage_ids}
        for row in rows:
            dispensed_map[str(row.cage_id)] = float(row.total_dispensed)

        return dispensed_map
