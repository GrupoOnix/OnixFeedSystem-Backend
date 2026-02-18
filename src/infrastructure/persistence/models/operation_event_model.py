"""
Modelo de persistencia para eventos de operación.
"""
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .feeding_operation_model import FeedingOperationModel


class OperationEventModel(SQLModel, table=True):
    """
    Modelo de persistencia para eventos de operación.
    Registra el ciclo de vida detallado de cada operación.
    """
    __tablename__ = "operation_events"

    # Primary Key
    id: UUID = Field(primary_key=True, default_factory=uuid4)

    # Foreign Key
    operation_id: UUID = Field(
        foreign_key="feeding_operations.id",
        index=True,
        ondelete="CASCADE"
    )

    # Datos del evento
    timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    type: str = Field(max_length=50)  # STARTED, PAUSED, RESUMED, PARAM_CHANGE, COMPLETED, STOPPED, FAILED
    description: str = Field(max_length=500)
    details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    # Relationship
    operation: Optional["FeedingOperationModel"] = Relationship(back_populates="events")

    class Config:
        arbitrary_types_allowed = True
