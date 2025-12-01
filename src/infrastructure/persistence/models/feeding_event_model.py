from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .feeding_session_model import FeedingSessionModel


class FeedingEventModel(SQLModel, table=True):
    __tablename__ = "feeding_events"

    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign Key with CASCADE delete
    session_id: UUID = Field(
        foreign_key="feeding_sessions.id",
        index=True,
        ondelete="CASCADE"
    )

    # Datos del evento
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    event_type: str = Field(max_length=50)  # COMMAND, PARAM_CHANGE, SYSTEM_STATUS, ALARM
    description: str = Field(max_length=500)
    details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    # Relationship
    session: Optional["FeedingSessionModel"] = Relationship(back_populates="events")

    class Config:
        arbitrary_types_allowed = True
