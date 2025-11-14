"""Modelo de persistencia para SlotAssignment."""

from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from domain.value_objects import CageId, SlotAssignment, SlotNumber


class SlotAssignmentModel(SQLModel, table=True):
    __tablename__ = "slot_assignments"

    id: UUID = Field(default_factory=lambda: __import__("uuid").uuid4(), primary_key=True)
    line_id: UUID = Field(foreign_key="feeding_lines.id", ondelete="CASCADE")
    slot_number: int
    cage_id: UUID = Field(foreign_key="cages.id")

    feeding_line: "FeedingLineModel" = Relationship(back_populates="slot_assignments")

    class Config:
        # Constraints únicos a nivel de BD
        table_args = (
            {"sqlite_autoincrement": True},
        )

    @staticmethod
    def from_domain(assignment: SlotAssignment, line_id: UUID) -> "SlotAssignmentModel":
        """Convierte VO de dominio a modelo de persistencia."""
        return SlotAssignmentModel(
            line_id=line_id,
            slot_number=assignment.slot_number.value,
            cage_id=assignment.cage_id.value,
        )

    def to_domain(self) -> SlotAssignment:
        """Convierte modelo de persistencia a VO de dominio."""
        return SlotAssignment(
            slot_number=SlotNumber(self.slot_number),
            cage_id=CageId(self.cage_id),
        )
