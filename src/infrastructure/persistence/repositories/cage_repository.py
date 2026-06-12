"""Implementación del repositorio de jaulas."""

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository
from domain.value_objects.identifiers import LineId
from domain.value_objects.identifiers import CageId
from domain.value_objects.names import CageName
from infrastructure.persistence.models.cage_model import CageModel
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel
from infrastructure.persistence.models.slot_assignment_model import SlotAssignmentModel


class CageRepository(ICageRepository):
    """Implementación SQLAlchemy del repositorio de jaulas."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, cage: Cage) -> None:
        """Guarda o actualiza una jaula."""
        existing = await self.session.get(CageModel, cage.id.value)

        if existing:
            # Actualizar campos
            existing.name = str(cage.name)
            existing.status = cage.status.value
            existing.created_at = cage.created_at

            # Población
            existing.fish_count = cage.fish_count
            existing.avg_weight_grams = cage.avg_weight_grams

            # Configuración
            existing.fcr = cage.config.fcr
            existing.volume_m3 = cage.config.volume_m3
            existing.max_density_kg_m3 = cage.config.max_density_kg_m3
            existing.transport_time_seconds = cage.config.transport_time_seconds
            existing.blower_power = cage.config.blower_power
            existing.daily_feeding_target_kg = cage.config.daily_feeding_target_kg
        else:
            cage_model = CageModel.from_domain(cage)
            self.session.add(cage_model)

        await self.session.flush()

    async def find_by_id(self, cage_id: CageId) -> Optional[Cage]:
        """Busca una jaula por su ID."""
        cage_model = await self.session.get(CageModel, cage_id.value)
        return cage_model.to_domain() if cage_model else None

    async def find_by_name(self, name: CageName) -> Optional[Cage]:
        """Busca una jaula por su nombre."""
        result = await self.session.execute(select(CageModel).where(col(CageModel.name) == str(name)))
        cage_model = result.scalar_one_or_none()
        return cage_model.to_domain() if cage_model else None

    async def list(self) -> List[Cage]:
        """Lista todas las jaulas."""
        result = await self.session.execute(select(CageModel).order_by(col(CageModel.name)))
        cage_models = result.scalars().all()
        return [model.to_domain() for model in cage_models]

    async def list_with_line_info(
        self, line_id: Optional[LineId] = None
    ) -> List[Tuple[Cage, Optional[str]]]:
        """Lista jaulas con el nombre de la línea asignada, si existe."""
        stmt = (
            select(CageModel, col(FeedingLineModel.name))
            .outerjoin(
                SlotAssignmentModel,
                col(SlotAssignmentModel.cage_id) == col(CageModel.id),
            )
            .outerjoin(
                FeedingLineModel,
                col(FeedingLineModel.id) == col(SlotAssignmentModel.line_id),
            )
            .order_by(col(CageModel.name))
        )

        if line_id is not None:
            stmt = stmt.where(col(SlotAssignmentModel.line_id) == line_id.value)

        result = await self.session.execute(stmt)
        return [
            (cage_model.to_domain(), line_name)
            for cage_model, line_name in result.all()
        ]

    async def delete(self, cage_id: CageId) -> None:
        """Elimina una jaula."""
        cage_model = await self.session.get(CageModel, cage_id.value)
        if cage_model:
            await self.session.delete(cage_model)
            await self.session.flush()

    async def exists(self, cage_id: CageId) -> bool:
        """Verifica si existe una jaula con el ID dado."""
        cage_model = await self.session.get(CageModel, cage_id.value)
        return cage_model is not None
