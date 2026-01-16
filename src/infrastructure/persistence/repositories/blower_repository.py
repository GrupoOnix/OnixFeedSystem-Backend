"""Repositorio para operaciones de Blower."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.aggregates.feeding_line.blower import Blower
from infrastructure.persistence.models.blower_model import BlowerModel


@dataclass
class BlowerWithContext:
    """Blower con información de contexto de su línea."""

    blower: Blower
    line_id: UUID
    line_name: str


class BlowerRepository:
    """Repositorio para acceso directo a blowers."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, blower_id: UUID) -> Optional[Blower]:
        """Busca un blower por su ID."""
        stmt = select(BlowerModel).where(BlowerModel.id == blower_id)
        result = await self.session.execute(stmt)
        blower_model = result.scalar_one_or_none()
        return blower_model.to_domain() if blower_model else None

    async def find_by_id_with_context(
        self, blower_id: UUID
    ) -> Optional[BlowerWithContext]:
        """Busca un blower por su ID y devuelve también información de la línea."""
        stmt = (
            select(BlowerModel)
            .options(selectinload(BlowerModel.feeding_line))
            .where(BlowerModel.id == blower_id)
        )
        result = await self.session.execute(stmt)
        blower_model = result.scalar_one_or_none()

        if not blower_model:
            return None

        return BlowerWithContext(
            blower=blower_model.to_domain(),
            line_id=blower_model.line_id,
            line_name=blower_model.feeding_line.name,
        )

    async def update(self, blower_id: UUID, blower: Blower) -> None:
        """Actualiza un blower existente."""
        stmt = select(BlowerModel).where(BlowerModel.id == blower_id)
        result = await self.session.execute(stmt)
        blower_model = result.scalar_one_or_none()

        if not blower_model:
            raise ValueError(f"Blower {blower_id} no encontrado")

        # Actualizar campos
        blower_model.name = str(blower.name)
        blower_model.power_percentage = blower.non_feeding_power.value
        blower_model.current_power_percentage = blower.current_power.value
        blower_model.blow_before_seconds = blower.blow_before_feeding_time.value
        blower_model.blow_after_seconds = blower.blow_after_feeding_time.value

        await self.session.flush()
