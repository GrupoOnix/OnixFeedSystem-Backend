"""Modelo de persistencia para Blower."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from domain.value_objects import (
    BlowDurationInSeconds,
    BlowerId,
    BlowerName,
    BlowerPowerPercentage,
)

if TYPE_CHECKING:
    from domain.aggregates.feeding_line.blower import Blower
    from domain.interfaces import IBlower


class BlowerModel(SQLModel, table=True):
    __tablename__ = "blowers"

    id: UUID = Field(primary_key=True)
    line_id: UUID = Field(foreign_key="feeding_lines.id", ondelete="CASCADE")
    name: str = Field(max_length=100)
    power_percentage: float
    current_power_percentage: float
    blow_before_seconds: int
    blow_after_seconds: int

    feeding_line: "FeedingLineModel" = Relationship(back_populates="blower")

    @staticmethod
    def from_domain(blower: "IBlower", line_id: UUID) -> "BlowerModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return BlowerModel(
            id=blower.id.value,
            line_id=line_id,
            name=str(blower.name),
            power_percentage=blower.non_feeding_power.value,
            current_power_percentage=blower.current_power.value,
            blow_before_seconds=blower.blow_before_feeding_time.value,
            blow_after_seconds=blower.blow_after_feeding_time.value,
        )

    def to_domain(self) -> "Blower":
        """Convierte modelo de persistencia a entidad de dominio."""
        # Import local para evitar circular imports pero tenerlo disponible en runtime
        from domain.aggregates.feeding_line.blower import Blower

        blower = Blower(
            name=BlowerName(self.name),
            non_feeding_power=BlowerPowerPercentage(self.power_percentage),
            blow_before_time=BlowDurationInSeconds(self.blow_before_seconds),
            blow_after_time=BlowDurationInSeconds(self.blow_after_seconds),
            current_power=BlowerPowerPercentage(self.current_power_percentage),
        )
        blower._id = BlowerId(self.id)
        return blower
