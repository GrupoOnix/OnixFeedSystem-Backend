"""Implementación del repositorio de eventos de población."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.population_event import PopulationEvent
from domain.enums import PopulationEventType
from domain.repositories import IPopulationEventRepository
from domain.value_objects.identifiers import CageId
from infrastructure.persistence.models.population_event_model import (
    PopulationEventModel,
)


class PopulationEventRepository(IPopulationEventRepository):
    """Implementación SQLAlchemy del repositorio de eventos de población."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, event: PopulationEvent) -> None:
        """Guarda un evento de población."""
        model = PopulationEventModel.from_domain(event)
        self.session.add(model)
        await self.session.flush()

    async def list_by_cage(
        self,
        cage_id: CageId,
        event_types: Optional[List[PopulationEventType]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PopulationEvent]:
        """Lista eventos de población de una jaula."""
        query = select(PopulationEventModel).where(
            PopulationEventModel.cage_id == cage_id.value
        )

        if event_types:
            type_values = [et.value for et in event_types]
            query = query.where(PopulationEventModel.event_type.in_(type_values))

        query = (
            query.order_by(
                PopulationEventModel.event_date.desc(),
                PopulationEventModel.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        models = result.scalars().all()

        return [model.to_domain() for model in models]

    async def count_by_cage(
        self,
        cage_id: CageId,
        event_types: Optional[List[PopulationEventType]] = None,
    ) -> int:
        """Cuenta eventos de una jaula."""
        query = select(func.count(PopulationEventModel.id)).where(
            PopulationEventModel.cage_id == cage_id.value
        )

        if event_types:
            type_values = [et.value for et in event_types]
            query = query.where(PopulationEventModel.event_type.in_(type_values))

        result = await self.session.execute(query)
        return result.scalar() or 0
