from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .feeding_event_model import FeedingEventModel


class FeedingSessionModel(SQLModel, table=True):
    __tablename__ = "feeding_sessions"

    # Primary Key
    id: UUID = Field(primary_key=True)

    # Foreign Keys & Indexes
    line_id: UUID = Field(index=True, foreign_key="feeding_lines.id")

    # Temporal
    date: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Estado
    status: str = Field(index=True)  # CREATED, RUNNING, PAUSED, COMPLETED, FAILED

    # Acumuladores
    total_dispensed_kg: float = Field(default=0.0)

    # JSON Fields (PostgreSQL JSONB)
    dispensed_by_slot: Dict[str, float] = Field(
        default_factory=dict,
        sa_column=Column(JSONB)
    )
    applied_strategy_config: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB)
    )

    # Relationship
    events: List["FeedingEventModel"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    class Config:
        arbitrary_types_allowed = True
