from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from domain.enums import ActivityLogCategory, ActivityLogEventType
from domain.value_objects.activity_log_entry import ActivityLogEntry
from domain.value_objects import CageId


class ActivityLogModel(SQLModel, table=True):
    __tablename__ = "cage_activity_log"

    log_id: UUID = Field(default_factory=uuid4, primary_key=True)
    cage_id: UUID = Field(foreign_key="cages.id", nullable=False, index=True, ondelete="CASCADE")
    event_type: str = Field(nullable=False, index=True)
    category: str = Field(nullable=False, index=True)
    message: str = Field(nullable=False)
    details: Optional[str] = Field(default=None)
    actor: Optional[str] = Field(default=None)
    source_entity_type: Optional[str] = Field(default=None)
    source_entity_id: Optional[str] = Field(default=None)
    event_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @staticmethod
    def from_domain(entry: ActivityLogEntry) -> "ActivityLogModel":
        """Convierte VO de dominio a modelo de persistencia."""
        return ActivityLogModel(
            log_id=entry.log_id,
            cage_id=entry.cage_id.value,
            event_type=entry.event_type.value,
            category=entry.category.value,
            message=entry.message,
            details=entry.details,
            actor=entry.actor,
            source_entity_type=entry.source_entity_type,
            source_entity_id=entry.source_entity_id,
            event_at=entry.event_at,
            created_at=entry.created_at,
        )

    def to_domain(self) -> ActivityLogEntry:
        """Convierte modelo de persistencia a VO de dominio."""
        return ActivityLogEntry(
            log_id=self.log_id,
            cage_id=CageId(self.cage_id),
            event_type=ActivityLogEventType(self.event_type),
            category=ActivityLogCategory(self.category),
            message=self.message,
            details=self.details,
            actor=self.actor,
            source_entity_type=self.source_entity_type,
            source_entity_id=self.source_entity_id,
            event_at=self.event_at,
            created_at=self.created_at,
        )
