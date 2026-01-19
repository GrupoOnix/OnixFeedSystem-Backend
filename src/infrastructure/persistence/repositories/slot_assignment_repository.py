"""Implementación del repositorio de asignaciones de slots."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.slot_assignment import SlotAssignment
from domain.repositories import ISlotAssignmentRepository
from domain.value_objects.identifiers import CageId, LineId
from infrastructure.persistence.models.slot_assignment_model import (
    SlotAssignmentModel,
)


class SlotAssignmentRepository(ISlotAssignmentRepository):
    """Implementación SQLAlchemy del repositorio de asignaciones de slots."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, assignment: SlotAssignment) -> None:
        """Guarda o actualiza una asignación."""
        existing = await self.session.get(SlotAssignmentModel, assignment.id)

        if existing:
            existing.line_id = assignment.line_id.value
            existing.cage_id = assignment.cage_id.value
            existing.slot_number = assignment.slot_number
            existing.assigned_at = assignment.assigned_at
        else:
            model = SlotAssignmentModel.from_domain(assignment)
            self.session.add(model)

        await self.session.flush()

    async def find_by_line_and_slot(
        self, line_id: LineId, slot_number: int
    ) -> Optional[SlotAssignment]:
        """Busca una asignación por línea y número de slot."""
        result = await self.session.execute(
            select(SlotAssignmentModel).where(
                SlotAssignmentModel.line_id == line_id.value,
                SlotAssignmentModel.slot_number == slot_number,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def find_by_cage(self, cage_id: CageId) -> Optional[SlotAssignment]:
        """Busca la asignación de una jaula."""
        result = await self.session.execute(
            select(SlotAssignmentModel).where(
                SlotAssignmentModel.cage_id == cage_id.value
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def find_by_line(self, line_id: LineId) -> List[SlotAssignment]:
        """Obtiene todas las asignaciones de una línea."""
        result = await self.session.execute(
            select(SlotAssignmentModel)
            .where(SlotAssignmentModel.line_id == line_id.value)
            .order_by(SlotAssignmentModel.slot_number)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def delete(self, assignment_id: UUID) -> None:
        """Elimina una asignación."""
        model = await self.session.get(SlotAssignmentModel, assignment_id)
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def delete_by_line(self, line_id: LineId) -> None:
        """Elimina todas las asignaciones de una línea."""
        await self.session.execute(
            delete(SlotAssignmentModel).where(
                SlotAssignmentModel.line_id == line_id.value
            )
        )
        await self.session.flush()

    async def delete_by_cage(self, cage_id: CageId) -> None:
        """Elimina la asignación de una jaula."""
        await self.session.execute(
            delete(SlotAssignmentModel).where(
                SlotAssignmentModel.cage_id == cage_id.value
            )
        )
        await self.session.flush()
