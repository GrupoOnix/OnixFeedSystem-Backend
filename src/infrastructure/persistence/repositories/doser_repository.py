"""Repositorio para operaciones de Doser."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.aggregates.feeding_line.doser import Doser
from infrastructure.persistence.models.doser_model import DoserModel


@dataclass
class DoserWithContext:
    """Doser con información de contexto de su línea."""

    doser: Doser
    line_id: UUID
    line_name: str


class DoserRepository:
    """Repositorio para acceso directo a dosers."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, doser_id: UUID) -> Optional[Doser]:
        """Busca un doser por su ID."""
        stmt = select(DoserModel).where(DoserModel.id == doser_id)
        result = await self.session.execute(stmt)
        doser_model = result.scalar_one_or_none()
        return doser_model.to_domain() if doser_model else None

    async def find_by_id_with_context(
        self, doser_id: UUID
    ) -> Optional[DoserWithContext]:
        """Busca un doser por su ID y devuelve también información de la línea."""
        stmt = (
            select(DoserModel)
            .options(selectinload(DoserModel.feeding_line))
            .where(DoserModel.id == doser_id)
        )
        result = await self.session.execute(stmt)
        doser_model = result.scalar_one_or_none()

        if not doser_model:
            return None

        return DoserWithContext(
            doser=doser_model.to_domain(),
            line_id=doser_model.line_id,
            line_name=doser_model.feeding_line.name,
        )

    async def update(self, doser_id: UUID, doser: Doser) -> None:
        """Actualiza un doser existente."""
        stmt = select(DoserModel).where(DoserModel.id == doser_id)
        result = await self.session.execute(stmt)
        doser_model = result.scalar_one_or_none()

        if not doser_model:
            raise ValueError(f"Doser {doser_id} no encontrado")

        # Actualizar campos
        doser_model.name = str(doser.name)
        doser_model.silo_id = doser.assigned_silo_id.value
        doser_model.doser_type = doser.doser_type.value
        doser_model.dosing_rate_value = doser.current_rate.value
        doser_model.dosing_rate_unit = doser.current_rate.unit
        doser_model.min_rate_value = doser.dosing_range.min_rate
        doser_model.max_rate_value = doser.dosing_range.max_rate
        doser_model.rate_unit = doser.dosing_range.unit
        doser_model.is_on = doser.is_on
        doser_model.speed_percentage = doser.speed_percentage

        await self.session.flush()
