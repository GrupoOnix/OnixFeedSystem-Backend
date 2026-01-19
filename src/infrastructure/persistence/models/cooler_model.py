"""Modelo de persistencia para Cooler."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from domain.value_objects import (
    CoolerId,
    CoolerName,
    CoolerPowerPercentage,
)

if TYPE_CHECKING:
    from domain.aggregates.feeding_line.cooler import Cooler
    from domain.interfaces import ICooler

    from .feeding_line_model import FeedingLineModel


class CoolerModel(SQLModel, table=True):
    __tablename__ = "coolers"

    id: UUID = Field(primary_key=True)
    line_id: UUID = Field(foreign_key="feeding_lines.id", ondelete="CASCADE")
    name: str = Field(max_length=100)
    is_on: bool = Field(default=False)
    cooling_power_percentage: float

    feeding_line: "FeedingLineModel" = Relationship(back_populates="cooler")

    @staticmethod
    def from_domain(cooler: "ICooler", line_id: UUID) -> "CoolerModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return CoolerModel(
            id=cooler.id.value,
            line_id=line_id,
            name=str(cooler.name),
            is_on=cooler.is_on,
            cooling_power_percentage=cooler.cooling_power_percentage.value,
        )

    def to_domain(self) -> "Cooler":
        """Convierte modelo de persistencia a entidad de dominio."""
        from domain.aggregates.feeding_line.cooler import Cooler

        cooler = Cooler(
            name=CoolerName(self.name),
            cooling_power_percentage=CoolerPowerPercentage(
                self.cooling_power_percentage
            ),
            is_on=self.is_on,
        )
        cooler._id = CoolerId(self.id)
        return cooler
