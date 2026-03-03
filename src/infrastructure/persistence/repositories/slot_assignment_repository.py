"""Implementación del repositorio de asignaciones de slots."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.slot_assignment import SlotAssignment
from domain.repositories import ISlotAssignmentRepository
from domain.value_objects.identifiers import CageId, LineId, UserId
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
            existing.user_id = assignment.user_id.value if assignment.user_id else None
        else:
            model = SlotAssignmentModel.from_domain(assignment)
            self.session.add(model)

        await self.session.flush()

    async def find_by_line_and_slot(
        self, line_id: LineId, slot_number: int, user_id: UserId
    ) -> Optional[SlotAssignment]:
        """Busca una asignación por línea y número de slot, filtrado por usuario."""
        result = await self.session.execute(
            select(SlotAssignmentModel).where(
                SlotAssignmentModel.line_id == line_id.value,
                SlotAssignmentModel.slot_number == slot_number,
                SlotAssignmentModel.user_id == user_id.value,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def find_by_cage(self, cage_id: CageId, user_id: UserId) -> Optional[SlotAssignment]:
        """Busca la asignación de una jaula, filtrado por usuario."""
        result = await self.session.execute(
            select(SlotAssignmentModel).where(
                SlotAssignmentModel.cage_id == cage_id.value,
                SlotAssignmentModel.user_id == user_id.value,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def find_by_line(self, line_id: LineId, user_id: UserId) -> List[SlotAssignment]:
        """Obtiene todas las asignaciones de una línea, filtrado por usuario."""
        result = await self.session.execute(
            select(SlotAssignmentModel)
            .where(
                SlotAssignmentModel.line_id == line_id.value,
                SlotAssignmentModel.user_id == user_id.value,
            )
            .order_by(SlotAssignmentModel.slot_number)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def delete(self, assignment_id: UUID, user_id: UserId) -> None:
        """Elimina una asignación del usuario."""
        result = await self.session.execute(
            select(SlotAssignmentModel).where(
                SlotAssignmentModel.id == assignment_id,
                SlotAssignmentModel.user_id == user_id.value,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def delete_by_line(self, line_id: LineId, user_id: UserId) -> None:
        """Elimina todas las asignaciones de una línea del usuario."""
        await self.session.execute(
            delete(SlotAssignmentModel).where(
                SlotAssignmentModel.line_id == line_id.value,
                SlotAssignmentModel.user_id == user_id.value,
            )
        )
        await self.session.flush()

    async def delete_by_cage(self, cage_id: CageId, user_id: UserId) -> None:
        """Elimina la asignación de una jaula del usuario."""
        await self.session.execute(
            delete(SlotAssignmentModel).where(
                SlotAssignmentModel.cage_id == cage_id.value,
                SlotAssignmentModel.user_id == user_id.value,
            )
        )
        await self.session.flush()
