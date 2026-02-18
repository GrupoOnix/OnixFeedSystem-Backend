"""Modelo de base de datos para eventos de alimentación."""

from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel, Relationship

from domain.entities.feeding_event import FeedingEvent, FeedingEventType

if TYPE_CHECKING:
    from .feeding_session_model import FeedingSessionModel


class FeedingEventModel(SQLModel, table=True):
    """Modelo SQLModel para eventos de sesiones de alimentación."""

    __tablename__ = "feeding_events"

    # Primary Key
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)

    # Foreign Keys
    feeding_session_id: str = Field(
        foreign_key="feeding_sessions.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )

    # Campos del evento
    event_type: str = Field(max_length=50, nullable=False, index=True)
    timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))

    # Datos flexibles en JSON
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    # Relaciones
    session: "FeedingSessionModel" = Relationship(back_populates="events")

    @staticmethod
    def from_domain(event: FeedingEvent) -> "FeedingEventModel":
        """Convierte una entidad de dominio a modelo de persistencia."""
        return FeedingEventModel(
            id=event.id,
            feeding_session_id=event.feeding_session_id,
            event_type=event.event_type.value,
            timestamp=event.timestamp,
            data=event.data,
        )

    def to_domain(self) -> FeedingEvent:
        """Convierte el modelo de persistencia a entidad de dominio."""
        # Reconstruir usando __new__ para evitar validaciones
        event = FeedingEvent.__new__(FeedingEvent)
        event._id = self.id
        event._feeding_session_id = self.feeding_session_id
        event._event_type = FeedingEventType(self.event_type)
        event._timestamp = self.timestamp
        event._data = self.data.copy() if self.data else {}

        return event
