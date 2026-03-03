"""Repositorio para operaciones de Selector."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.aggregates.feeding_line.selector import Selector
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel
from infrastructure.persistence.models.selector_model import SelectorModel


@dataclass
class SelectorWithContext:
    """Selector con información de contexto de su línea."""

    selector: Selector
    line_id: UUID
    line_name: str


class SelectorRepository:
    """Repositorio para acceso directo a selectors."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, selector_id: UUID, user_id: Optional[UUID] = None) -> Optional[Selector]:
        """Busca un selector por su ID, opcionalmente filtrado por user_id."""
        stmt = select(SelectorModel).where(SelectorModel.id == selector_id)
        if user_id is not None:
            stmt = stmt.join(FeedingLineModel).where(FeedingLineModel.user_id == user_id)
        result = await self.session.execute(stmt)
        selector_model = result.scalar_one_or_none()
        return selector_model.to_domain() if selector_model else None

    async def find_by_id_with_context(
        self, selector_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[SelectorWithContext]:
        """Busca un selector por su ID y devuelve también información de la línea.

        Si se proporciona user_id, verifica que el selector pertenezca a una línea del usuario.
        """
        stmt = (
            select(SelectorModel)
            .options(selectinload(SelectorModel.feeding_line))
            .where(SelectorModel.id == selector_id)
        )
        if user_id is not None:
            stmt = stmt.join(FeedingLineModel).where(FeedingLineModel.user_id == user_id)
        result = await self.session.execute(stmt)
        selector_model = result.scalar_one_or_none()

        if not selector_model:
            return None

        return SelectorWithContext(
            selector=selector_model.to_domain(),
            line_id=selector_model.line_id,
            line_name=selector_model.feeding_line.name,
        )

    async def update(self, selector_id: UUID, selector: Selector) -> None:
        """Actualiza un selector existente."""
        stmt = select(SelectorModel).where(SelectorModel.id == selector_id)
        result = await self.session.execute(stmt)
        selector_model = result.scalar_one_or_none()

        if not selector_model:
            raise ValueError(f"Selector {selector_id} no encontrado")

        # Actualizar campos
        selector_model.name = str(selector.name)
        selector_model.capacity = selector.capacity.value
        selector_model.fast_speed = selector.speed_profile.fast_speed.value
        selector_model.slow_speed = selector.speed_profile.slow_speed.value
        selector_model.current_slot = selector.current_slot

        await self.session.flush()
