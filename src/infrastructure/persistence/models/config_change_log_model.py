from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel

from domain.value_objects.config_change_log_entry import ConfigChangeLogEntry
from domain.value_objects import CageId


class ConfigChangeLogModel(SQLModel, table=True):
    __tablename__ = "cage_config_changes_log"

    change_id: UUID = Field(default_factory=uuid4, primary_key=True)
    cage_id: UUID = Field(foreign_key="cages.id", nullable=False, index=True, ondelete="CASCADE")
    
    field_name: str = Field(nullable=False, max_length=50)
    old_value: str = Field(nullable=False)
    new_value: str = Field(nullable=False)
    change_reason: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    @staticmethod
    def from_domain(entry: ConfigChangeLogEntry) -> "ConfigChangeLogModel":
        """Convierte VO de dominio a modelo de persistencia."""
        return ConfigChangeLogModel(
            change_id=entry.change_id,
            cage_id=entry.cage_id.value,
            field_name=entry.field_name,
            old_value=entry.old_value,
            new_value=entry.new_value,
            change_reason=entry.change_reason,
            created_at=entry.created_at,
        )

    def to_domain(self) -> ConfigChangeLogEntry:
        """Convierte modelo de persistencia a VO de dominio."""
        return ConfigChangeLogEntry(
            change_id=self.change_id,
            cage_id=CageId(self.cage_id),
            field_name=self.field_name,
            old_value=self.old_value,
            new_value=self.new_value,
            change_reason=self.change_reason,
            created_at=self.created_at,
        )
