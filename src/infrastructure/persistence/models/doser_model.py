from typing import TYPE_CHECKING, List, Optional
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
from .doser_silo_model import DoserSiloModel

if TYPE_CHECKING:
    from domain.aggregates.feeding_line.doser import Doser
    from domain.interfaces import IDoser

    from .feeding_line_model import FeedingLineModel
    from .silo_model import SiloModel


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
    is_on: bool = Field(default=False)
    speed_percentage: int = Field(default=50)
    calibrated_grams_per_second: Optional[float] = Field(default=None)
    pulse_on_time: Optional[float] = Field(default=None)
    pulse_off_time: Optional[float] = Field(default=None)
    pulse_speed: Optional[int] = Field(default=None)

    feeding_line: "FeedingLineModel" = Relationship(back_populates="dosers")
    silos: List["SiloModel"] = Relationship(
        back_populates="dosers",
        link_model=DoserSiloModel,
    )

    @staticmethod
    def from_domain(doser: "IDoser", line_id: UUID) -> "DoserModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return DoserModel(
            id=doser.id.value,
            line_id=line_id,
            name=str(doser.name),
            silo_id=None,
            doser_type=doser.doser_type.value,
            dosing_rate_value=doser.current_rate.value,
            dosing_rate_unit=doser.current_rate.unit,
            min_rate_value=doser.dosing_range.min_rate,
            max_rate_value=doser.dosing_range.max_rate,
            rate_unit=doser.dosing_range.unit,
            is_on=doser.is_on,
            speed_percentage=doser.speed_percentage,
            calibrated_grams_per_second=doser.calibrated_grams_per_second,
            pulse_on_time=doser.pulse_on_time,
            pulse_off_time=doser.pulse_off_time,
            pulse_speed=doser.pulse_speed,
        )

    def to_domain(self) -> "Doser":
        """Convierte modelo de persistencia a entidad de dominio."""
        # Import local para evitar circular imports pero tenerlo disponible en runtime
        from domain.aggregates.feeding_line.doser import Doser

        silo_ids = [silo.id for silo in self.silos]
        if not silo_ids and self.silo_id:
            silo_ids = [self.silo_id]

        if not silo_ids:
            raise ValueError("Doser debe tener un silo asignado")

        doser = Doser(
            name=DoserName(self.name),
            assigned_silo_ids=[SiloId(silo_id) for silo_id in silo_ids],
            doser_type=DoserType(self.doser_type),
            dosing_range=DosingRange(
                min_rate=self.min_rate_value,
                max_rate=self.max_rate_value,
                unit=self.rate_unit,
            ),
            current_rate=DosingRate(value=self.dosing_rate_value, unit=self.dosing_rate_unit),
            is_on=self.is_on,
            speed_percentage=self.speed_percentage,
            calibrated_grams_per_second=self.calibrated_grams_per_second,
            pulse_on_time=self.pulse_on_time,
            pulse_off_time=self.pulse_off_time,
            pulse_speed=self.pulse_speed,
            _skip_validation=True,  # Permitir cargar dosers con rate=0 desde DB
        )
        doser._id = DoserId(self.id)
        return doser
