"""Modelo de base de datos para eventos de población."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from domain.entities.population_event import PopulationEvent
from domain.enums import PopulationEventType
from domain.value_objects.identifiers import CageId


class PopulationEventModel(SQLModel, table=True):
    """Modelo SQLModel para eventos de población de jaulas."""

    __tablename__ = "cage_population_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    cage_id: UUID = Field(
        foreign_key="cages.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )

    event_type: str = Field(max_length=20)
    event_date: date
    fish_count_delta: int
    new_fish_count: int
    avg_weight_grams: Optional[float] = Field(default=None)
    note: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    @staticmethod
    def from_domain(event: PopulationEvent) -> "PopulationEventModel":
        """Convierte una entidad de dominio a modelo de persistencia."""
        return PopulationEventModel(
            id=event.id,
            cage_id=event.cage_id.value,
            event_type=event.event_type.value,
            event_date=event.event_date,
            fish_count_delta=event.fish_count_delta,
            new_fish_count=event.new_fish_count,
            avg_weight_grams=event.avg_weight_grams,
            note=event.note,
            created_at=event.created_at,
        )

    def to_domain(self) -> PopulationEvent:
        """Convierte el modelo de persistencia a entidad de dominio."""
        return PopulationEvent(
            id=self.id,
            cage_id=CageId(self.cage_id),
            event_type=PopulationEventType(self.event_type),
            event_date=self.event_date,
            fish_count_delta=self.fish_count_delta,
            new_fish_count=self.new_fish_count,
            avg_weight_grams=self.avg_weight_grams,
            note=self.note,
            created_at=self.created_at,
        )
