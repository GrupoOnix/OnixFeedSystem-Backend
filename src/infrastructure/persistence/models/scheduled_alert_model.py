"""Modelo de persistencia para ScheduledAlert."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from domain.aggregates.scheduled_alert import ScheduledAlert
from domain.enums import AlertCategory, AlertType, ScheduledAlertFrequency
from domain.value_objects import ScheduledAlertId


class ScheduledAlertModel(SQLModel, table=True):
    """Modelo de persistencia para alertas programadas."""

    __tablename__ = "scheduled_alerts"

    id: UUID = Field(primary_key=True)
    title: str = Field(max_length=200)
    message: str = Field(sa_column=Column(Text, nullable=False))
    type: str
    category: str
    frequency: str
    next_trigger_date: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    days_before_warning: int = Field(default=0)
    is_active: bool = Field(default=True, index=True)
    device_id: Optional[str] = Field(default=None, max_length=100)
    device_name: Optional[str] = Field(default=None, max_length=200)
    custom_days_interval: Optional[int] = Field(default=None)
    metadata_json: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column("metadata", JSONB, nullable=False)
    )
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    last_triggered_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def from_domain(scheduled_alert: ScheduledAlert) -> "ScheduledAlertModel":
        """Convierte aggregate de dominio a modelo de persistencia."""
        return ScheduledAlertModel(
            id=scheduled_alert.id.value,
            title=scheduled_alert.title,
            message=scheduled_alert.message,
            type=scheduled_alert.type.value,
            category=scheduled_alert.category.value,
            frequency=scheduled_alert.frequency.value,
            next_trigger_date=scheduled_alert.next_trigger_date,
            days_before_warning=scheduled_alert.days_before_warning,
            is_active=scheduled_alert.is_active,
            device_id=scheduled_alert.device_id,
            device_name=scheduled_alert.device_name,
            custom_days_interval=scheduled_alert.custom_days_interval,
            metadata_json=scheduled_alert.metadata,
            created_at=scheduled_alert.created_at,
            last_triggered_at=scheduled_alert.last_triggered_at,
        )

    def to_domain(self) -> ScheduledAlert:
        """Convierte modelo de persistencia a aggregate de dominio."""
        return ScheduledAlert.reconstitute(
            id=ScheduledAlertId(self.id),
            title=self.title,
            message=self.message,
            type=AlertType(self.type),
            category=AlertCategory(self.category),
            frequency=ScheduledAlertFrequency(self.frequency),
            next_trigger_date=self.next_trigger_date,
            days_before_warning=self.days_before_warning,
            is_active=self.is_active,
            created_at=self.created_at,
            device_id=self.device_id,
            device_name=self.device_name,
            custom_days_interval=self.custom_days_interval,
            metadata=self.metadata_json,
            last_triggered_at=self.last_triggered_at,
        )
