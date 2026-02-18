"""Modelo de base de datos para asignaciones de slots."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from domain.entities.slot_assignment import SlotAssignment
from domain.value_objects.identifiers import CageId, LineId


class SlotAssignmentModel(SQLModel, table=True):
    """Modelo SQLModel para asignaciones de jaulas a slots."""

    __tablename__ = "slot_assignments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    line_id: UUID = Field(
        foreign_key="feeding_lines.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    cage_id: UUID = Field(
        foreign_key="cages.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    slot_number: int = Field(nullable=False)
    assigned_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @staticmethod
    def from_domain(assignment: SlotAssignment) -> "SlotAssignmentModel":
        """Convierte una entidad de dominio a modelo de persistencia."""
        return SlotAssignmentModel(
            id=assignment.id,
            line_id=assignment.line_id.value,
            cage_id=assignment.cage_id.value,
            slot_number=assignment.slot_number,
            assigned_at=assignment.assigned_at,
        )

    def to_domain(self) -> SlotAssignment:
        """Convierte el modelo de persistencia a entidad de dominio."""
        return SlotAssignment(
            id=self.id,
            line_id=LineId(self.line_id),
            cage_id=CageId(self.cage_id),
            slot_number=self.slot_number,
            assigned_at=self.assigned_at,
        )
