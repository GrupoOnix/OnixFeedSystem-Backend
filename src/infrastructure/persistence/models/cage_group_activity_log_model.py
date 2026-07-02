from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from domain.enums import ActivityLogCategory, ActivityLogEventType
from domain.value_objects import CageGroupId
from domain.value_objects.cage_group_activity_log_entry import CageGroupActivityLogEntry


class CageGroupActivityLogModel(SQLModel, table=True):
    __tablename__ = "cage_group_activity_log"

    log_id: UUID = Field(default_factory=uuid4, primary_key=True)
    cage_group_id: UUID = Field(foreign_key="cage_groups.id", nullable=False, index=True, ondelete="CASCADE")
    event_type: str = Field(nullable=False, index=True)
    category: str = Field(nullable=False, index=True)
    message: str = Field(nullable=False)
    details: Optional[str] = Field(default=None)
    actor: Optional[str] = Field(default=None)
    event_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @staticmethod
    def from_domain(entry: CageGroupActivityLogEntry) -> "CageGroupActivityLogModel":
        """Convierte VO de dominio a modelo de persistencia."""
        return CageGroupActivityLogModel(
            log_id=entry.log_id,
            cage_group_id=entry.cage_group_id.value,
            event_type=entry.event_type.value,
            category=entry.category.value,
            message=entry.message,
            details=entry.details,
            actor=entry.actor,
            event_at=entry.event_at,
            created_at=entry.created_at,
        )

    def to_domain(self) -> CageGroupActivityLogEntry:
        """Convierte modelo de persistencia a VO de dominio."""
        return CageGroupActivityLogEntry(
            log_id=self.log_id,
            cage_group_id=CageGroupId(self.cage_group_id),
            event_type=ActivityLogEventType(self.event_type),
            category=ActivityLogCategory(self.category),
            message=self.message,
            details=self.details,
            actor=self.actor,
            event_at=self.event_at,
            created_at=self.created_at,
        )
