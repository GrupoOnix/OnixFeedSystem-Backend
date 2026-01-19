"""Modelo de persistencia para Alert."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from domain.aggregates.alert import Alert
from domain.enums import AlertCategory, AlertStatus, AlertType
from domain.value_objects import AlertId


class AlertModel(SQLModel, table=True):
    """Modelo de persistencia para alertas del sistema."""

    __tablename__ = "alerts"

    id: UUID = Field(primary_key=True)
    type: str = Field(index=True)
    status: str = Field(index=True)
    category: str = Field(index=True)
    title: str = Field(max_length=200)
    message: str = Field(sa_column=Column(Text, nullable=False))
    source: Optional[str] = Field(default=None, max_length=200)
    timestamp: datetime = Field(index=True)
    read_at: Optional[datetime] = Field(default=None)
    resolved_at: Optional[datetime] = Field(default=None)
    resolved_by: Optional[str] = Field(default=None, max_length=100)
    metadata_json: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column("metadata", JSONB, nullable=False)
    )

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def from_domain(alert: Alert) -> "AlertModel":
        """Convierte aggregate de dominio a modelo de persistencia."""
        return AlertModel(
            id=alert.id.value,
            type=alert.type.value,
            status=alert.status.value,
            category=alert.category.value,
            title=alert.title,
            message=alert.message,
            source=alert.source,
            timestamp=alert.timestamp,
            read_at=alert.read_at,
            resolved_at=alert.resolved_at,
            resolved_by=alert.resolved_by,
            metadata_json=alert.metadata,
        )

    def to_domain(self) -> Alert:
        """Convierte modelo de persistencia a aggregate de dominio."""
        return Alert.reconstitute(
            id=AlertId(self.id),
            type=AlertType(self.type),
            status=AlertStatus(self.status),
            category=AlertCategory(self.category),
            title=self.title,
            message=self.message,
            timestamp=self.timestamp,
            source=self.source,
            read_at=self.read_at,
            resolved_at=self.resolved_at,
            resolved_by=self.resolved_by,
            metadata=self.metadata_json,
        )
