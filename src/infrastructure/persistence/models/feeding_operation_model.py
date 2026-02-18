"""
Modelo de persistencia para operaciones de alimentación.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .feeding_session_model import FeedingSessionModel
    from .operation_event_model import OperationEventModel


class FeedingOperationModel(SQLModel, table=True):
    """
    Modelo de persistencia para operaciones de alimentación.
    Una operación representa una visita a una jaula (de START a STOP).
    """
    __tablename__ = "feeding_operations"

    # Primary Key
    id: UUID = Field(primary_key=True)

    # Foreign Keys
    session_id: UUID = Field(foreign_key="feeding_sessions.id", index=True, ondelete="CASCADE")
    cage_id: Optional[UUID] = Field(foreign_key="cages.id", index=True, ondelete="SET NULL")

    # Datos de la operación
    target_slot: int
    target_amount_kg: float
    dispensed_kg: float = Field(default=0.0)
    status: str = Field(index=True)  # RUNNING, PAUSED, COMPLETED, STOPPED, FAILED
    started_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    ended_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    applied_config: Dict[str, Any] = Field(sa_column=Column(JSONB))

    # Relationships
    session: "FeedingSessionModel" = Relationship(back_populates="operations")
    events: List["OperationEventModel"] = Relationship(
        back_populates="operation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    class Config:
        arbitrary_types_allowed = True
