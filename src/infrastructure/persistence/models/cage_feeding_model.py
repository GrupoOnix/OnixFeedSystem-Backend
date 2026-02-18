"""Modelo de base de datos para alimentación de jaulas."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from datetime import timezone
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, Relationship

from domain.entities.cage_feeding import CageFeeding, CageFeedingMode, CageFeedingStatus

if TYPE_CHECKING:
    from .feeding_session_model import FeedingSessionModel
    from .cage_model import CageModel


class CageFeedingModel(SQLModel, table=True):
    """Modelo SQLModel para alimentación de jaulas dentro de una sesión."""

    __tablename__ = "cage_feedings"

    # Primary Key
    id: str = Field(primary_key=True)

    # Foreign Keys
    feeding_session_id: str = Field(
        foreign_key="feeding_sessions.id",
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

    # Configuración
    execution_order: int = Field(nullable=False)
    mode: str = Field(max_length=20, nullable=False)
    programmed_kg: float = Field(nullable=False)
    programmed_visits: int = Field(nullable=False)
    rate_kg_per_min: float = Field(nullable=False)

    # Progreso
    dispensed_kg: float = Field(default=0.0)
    completed_visits: int = Field(default=0)
    status: str = Field(max_length=20, nullable=False, index=True)

    # Timestamps
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))

    # Relaciones
    session: "FeedingSessionModel" = Relationship(back_populates="cage_feedings")
    cage: "CageModel" = Relationship()

    @staticmethod
    def from_domain(cage_feeding: CageFeeding) -> "CageFeedingModel":
        """Convierte una entidad de dominio a modelo de persistencia."""
        return CageFeedingModel(
            id=cage_feeding.id,
            feeding_session_id=cage_feeding.feeding_session_id,
            cage_id=UUID(cage_feeding.cage_id),
            execution_order=cage_feeding.execution_order,
            mode=cage_feeding.mode.value,
            programmed_kg=cage_feeding.programmed_kg,
            programmed_visits=cage_feeding.programmed_visits,
            rate_kg_per_min=cage_feeding.rate_kg_per_min,
            dispensed_kg=cage_feeding.dispensed_kg,
            completed_visits=cage_feeding.completed_visits,
            status=cage_feeding.status.value,
            created_at=datetime.now(timezone.utc),
        )

    def to_domain(self) -> CageFeeding:
        """Convierte el modelo de persistencia a entidad de dominio."""
        # Reconstruir usando __new__ para evitar validaciones
        cage_feeding = CageFeeding.__new__(CageFeeding)
        cage_feeding._id = self.id
        cage_feeding._feeding_session_id = self.feeding_session_id
        cage_feeding._cage_id = str(self.cage_id)
        cage_feeding._execution_order = self.execution_order
        cage_feeding._mode = CageFeedingMode(self.mode)
        cage_feeding._programmed_kg = self.programmed_kg
        cage_feeding._programmed_visits = self.programmed_visits
        cage_feeding._rate_kg_per_min = self.rate_kg_per_min
        cage_feeding._dispensed_kg = self.dispensed_kg
        cage_feeding._completed_visits = self.completed_visits
        cage_feeding._status = CageFeedingStatus(self.status)

        return cage_feeding
