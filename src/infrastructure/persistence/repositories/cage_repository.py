"""Implementación del repositorio de jaulas."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository
from domain.value_objects.identifiers import CageId, UserId
from domain.value_objects.names import CageName
from infrastructure.persistence.models.cage_model import CageModel


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

            # Multi-usuario
            existing.user_id = cage.user_id.value if cage.user_id else existing.user_id
        else:
            cage_model = CageModel.from_domain(cage)
            self.session.add(cage_model)

        await self.session.flush()

    async def find_by_id(self, cage_id: CageId, user_id: UserId) -> Optional[Cage]:
        """Busca una jaula por su ID, filtrado por usuario."""
        result = await self.session.execute(
            select(CageModel).where(
                CageModel.id == cage_id.value,
                CageModel.user_id == user_id.value,
            )
        )
        cage_model = result.scalar_one_or_none()
        return cage_model.to_domain() if cage_model else None

    async def find_by_name(self, name: CageName, user_id: UserId) -> Optional[Cage]:
        """Busca una jaula por su nombre, filtrado por usuario."""
        result = await self.session.execute(
            select(CageModel).where(
                CageModel.name == str(name),
                CageModel.user_id == user_id.value,
            )
        )
        cage_model = result.scalar_one_or_none()
        return cage_model.to_domain() if cage_model else None

    async def list(self, user_id: UserId) -> List[Cage]:
        """Lista todas las jaulas de un usuario."""
        result = await self.session.execute(
            select(CageModel).where(CageModel.user_id == user_id.value).order_by(CageModel.name)
        )
        cage_models = result.scalars().all()
        return [model.to_domain() for model in cage_models]

    async def delete(self, cage_id: CageId, user_id: UserId) -> None:
        """Elimina una jaula del usuario."""
        result = await self.session.execute(
            select(CageModel).where(
                CageModel.id == cage_id.value,
                CageModel.user_id == user_id.value,
            )
        )
        cage_model = result.scalar_one_or_none()
        if cage_model:
            await self.session.delete(cage_model)
            await self.session.flush()

    async def exists(self, cage_id: CageId, user_id: UserId) -> bool:
        """Verifica si existe una jaula con el ID dado para el usuario."""
        result = await self.session.execute(
            select(CageModel).where(
                CageModel.id == cage_id.value,
                CageModel.user_id == user_id.value,
            )
        )
        cage_model = result.scalar_one_or_none()
        return cage_model is not None
