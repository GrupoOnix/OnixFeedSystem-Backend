from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from domain.value_objects import (
    BlowerPowerPercentage,
    SelectorCapacity,
    SelectorId,
    SelectorName,
    SelectorSpeedProfile,
)

if TYPE_CHECKING:
    from domain.aggregates.feeding_line.selector import Selector
    from domain.interfaces import ISelector

    from .feeding_line_model import FeedingLineModel


class SelectorModel(SQLModel, table=True):
    __tablename__ = "selectors"

    id: UUID = Field(primary_key=True)
    line_id: UUID = Field(foreign_key="feeding_lines.id", ondelete="CASCADE")
    name: str = Field(max_length=100)
    capacity: int
    fast_speed: float
    slow_speed: float
    current_slot: int | None = Field(default=None, nullable=True)

    feeding_line: "FeedingLineModel" = Relationship(back_populates="selector")

    @staticmethod
    def from_domain(selector: "ISelector", line_id: UUID) -> "SelectorModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return SelectorModel(
            id=selector.id.value,
            line_id=line_id,
            name=str(selector.name),
            capacity=selector.capacity.value,
            fast_speed=selector.speed_profile.fast_speed.value,
            slow_speed=selector.speed_profile.slow_speed.value,
            current_slot=selector.current_slot,
        )

    def to_domain(self) -> "Selector":
        """Convierte modelo de persistencia a entidad de dominio."""
        # Import local para evitar circular imports pero tenerlo disponible en runtime
        from domain.aggregates.feeding_line.selector import Selector

        selector = Selector(
            name=SelectorName(self.name),
            capacity=SelectorCapacity(self.capacity),
            speed_profile=SelectorSpeedProfile(
                fast_speed=BlowerPowerPercentage(self.fast_speed),
                slow_speed=BlowerPowerPercentage(self.slow_speed),
            ),
            current_slot=self.current_slot,
        )
        selector._id = SelectorId(self.id)
        return selector
