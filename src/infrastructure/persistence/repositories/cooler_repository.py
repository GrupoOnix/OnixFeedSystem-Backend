"""Repositorio para operaciones de Cooler."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.aggregates.feeding_line.cooler import Cooler
from infrastructure.persistence.models.cooler_model import CoolerModel


@dataclass
class CoolerWithContext:
    """Cooler con información de contexto de su línea."""

    cooler: Cooler
    line_id: UUID
    line_name: str


class CoolerRepository:
    """Repositorio para acceso directo a coolers."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, cooler_id: UUID) -> Optional[Cooler]:
        """Busca un cooler por su ID."""
        stmt = select(CoolerModel).where(CoolerModel.id == cooler_id)
        result = await self.session.execute(stmt)
        cooler_model = result.scalar_one_or_none()
        return cooler_model.to_domain() if cooler_model else None

    async def find_by_id_with_context(
        self, cooler_id: UUID
    ) -> Optional[CoolerWithContext]:
        """Busca un cooler por su ID y devuelve también información de la línea."""
        stmt = (
            select(CoolerModel)
            .options(selectinload(CoolerModel.feeding_line))
            .where(CoolerModel.id == cooler_id)
        )
        result = await self.session.execute(stmt)
        cooler_model = result.scalar_one_or_none()

        if not cooler_model:
            return None

        return CoolerWithContext(
            cooler=cooler_model.to_domain(),
            line_id=cooler_model.line_id,
            line_name=cooler_model.feeding_line.name,
        )

    async def update(self, cooler_id: UUID, cooler: Cooler) -> None:
        """Actualiza un cooler existente."""
        stmt = select(CoolerModel).where(CoolerModel.id == cooler_id)
        result = await self.session.execute(stmt)
        cooler_model = result.scalar_one_or_none()

        if not cooler_model:
            raise ValueError(f"Cooler {cooler_id} no encontrado")

        # Actualizar campos
        cooler_model.name = str(cooler.name)
        cooler_model.is_on = cooler.is_on
        cooler_model.cooling_power_percentage = cooler.cooling_power_percentage.value

        await self.session.flush()
