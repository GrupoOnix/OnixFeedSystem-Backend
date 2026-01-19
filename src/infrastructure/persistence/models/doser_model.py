from typing import TYPE_CHECKING, Optional
from uuid import UUID
from sqlmodel import Field, Relationship, SQLModel

from domain.enums import DoserType
from domain.value_objects import (
    DoserId,
    DoserName,
    DosingRange,
    DosingRate,
    SiloId,
)

if TYPE_CHECKING:
    from domain.aggregates.feeding_line.doser import Doser
    from domain.interfaces import IDoser


class DoserModel(SQLModel, table=True):
    __tablename__ = "dosers"

    id: UUID = Field(primary_key=True)
    line_id: UUID = Field(foreign_key="feeding_lines.id", ondelete="CASCADE")
    name: str = Field(max_length=100)
    silo_id: Optional[UUID] = Field(default=None, foreign_key="silos.id", ondelete="SET NULL")
    doser_type: str
    dosing_rate_value: float
    dosing_rate_unit: str
    min_rate_value: float
    max_rate_value: float
    rate_unit: str
    is_on: bool = Field(default=True)

    feeding_line: "FeedingLineModel" = Relationship(back_populates="dosers")

    @staticmethod
    def from_domain(doser: "IDoser", line_id: UUID) -> "DoserModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return DoserModel(
            id=doser.id.value,
            line_id=line_id,
            name=str(doser.name),
            silo_id=doser.assigned_silo_id.value,
            doser_type=doser.doser_type.value,
            dosing_rate_value=doser.current_rate.value,
            dosing_rate_unit=doser.current_rate.unit,
            min_rate_value=doser.dosing_range.min_rate,
            max_rate_value=doser.dosing_range.max_rate,
            rate_unit=doser.dosing_range.unit,
            is_on=doser.is_on,
        )

    def to_domain(self) -> "Doser":
        """Convierte modelo de persistencia a entidad de dominio."""
        # Import local para evitar circular imports pero tenerlo disponible en runtime
        from domain.aggregates.feeding_line.doser import Doser

        if not self.silo_id:
            raise ValueError("Doser debe tener un silo asignado")

        doser = Doser(
            name=DoserName(self.name),
            assigned_silo_id=SiloId(self.silo_id),
            doser_type=DoserType(self.doser_type),
            dosing_range=DosingRange(
                min_rate=self.min_rate_value,
                max_rate=self.max_rate_value,
                unit=self.rate_unit,
            ),
            current_rate=DosingRate(
                value=self.dosing_rate_value, unit=self.dosing_rate_unit
            ),
            is_on=self.is_on,
            _skip_validation=True,  # Permitir cargar dosers con rate=0 desde DB
        )
        doser._id = DoserId(self.id)
        return doser
