"""Modelo de base de datos para sesiones de alimentación."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from datetime import timezone
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, Relationship

from domain.entities.feeding_session import FeedingSession, FeedingType, SessionStatus

if TYPE_CHECKING:
    from .cage_feeding_model import CageFeedingModel
    from .feeding_event_model import FeedingEventModel
    from .feeding_line_model import FeedingLineModel


class FeedingSessionModel(SQLModel, table=True):
    """Modelo SQLModel para sesiones de alimentación."""

    __tablename__ = "feeding_sessions"

    # Primary Key
    id: str = Field(primary_key=True)

    # Foreign Keys
    line_id: UUID = Field(
        foreign_key="feeding_lines.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    operator_id: str = Field(nullable=False, index=True)

    # Tipo y Estado
    type: str = Field(max_length=20, nullable=False, index=True)
    status: str = Field(max_length=20, nullable=False, index=True)

    # Configuración
    allow_overtime: bool = Field(default=False)

    # Cantidades
    total_programmed_kg: float = Field(nullable=False)

    # Timestamps
    scheduled_start: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    actual_start: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True, index=True))
    actual_end: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))

    # Relaciones
    line: "FeedingLineModel" = Relationship(back_populates="feeding_sessions")
    cage_feedings: List["CageFeedingModel"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    events: List["FeedingEventModel"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    @staticmethod
    def from_domain(session: FeedingSession) -> "FeedingSessionModel":
        """Convierte una entidad de dominio a modelo de persistencia."""
        return FeedingSessionModel(
            id=session.id,
            line_id=UUID(session.line_id),
            operator_id=session.operator_id,
            type=session.type.value,
            status=session.status.value,
            allow_overtime=session.allow_overtime,
            total_programmed_kg=session.total_programmed_kg,
            scheduled_start=session.scheduled_start,
            actual_start=session.actual_start,
            actual_end=session.actual_end,
            created_at=datetime.now(timezone.utc),
        )

    def to_domain(self) -> FeedingSession:
        """Convierte el modelo de persistencia a entidad de dominio."""
        # Reconstruir la sesión usando __new__ para evitar validaciones
        session = FeedingSession.__new__(FeedingSession)
        session._id = self.id
        session._line_id = str(self.line_id)
        session._operator_id = self.operator_id
        session._type = FeedingType(self.type)
        session._status = SessionStatus(self.status)
        session._allow_overtime = self.allow_overtime
        session._total_programmed_kg = self.total_programmed_kg
        session._scheduled_start = self.scheduled_start
        session._actual_start = self.actual_start
        session._actual_end = self.actual_end

        # Convertir relaciones si ya están cargadas por selectinload
        session._cage_feedings = [cf.to_domain() for cf in self.cage_feedings] if self.cage_feedings else []
        session._events = []

        return session
