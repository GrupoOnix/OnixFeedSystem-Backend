"""Persistencia de planes diarios de alimentación programada."""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class ScheduledFeedingPlanModel(SQLModel, table=True):
    """Un plan diario ya calculado, independiente de una pestaña del navegador."""

    __tablename__ = "scheduled_feeding_plans"
    __table_args__ = (
        UniqueConstraint("line_id", name="uq_scheduled_feeding_plans_line_id"),
        Index("ix_scheduled_feeding_plans_line_start", "line_id", "start_time"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    line_id: UUID = Field(foreign_key="feeding_lines.id", nullable=False, ondelete="CASCADE")
    group_id: UUID = Field(nullable=False)
    doser_id: UUID = Field(nullable=False)
    silo_id: UUID = Field(nullable=False)
    name: str = Field(max_length=120, nullable=False)
    start_time: str = Field(max_length=5, nullable=False)
    end_time: str = Field(max_length=5, nullable=False)
    timezone: str = Field(default="America/Santiago", max_length=64, nullable=False)
    blower_power_percentage: float = Field(default=70.0, nullable=False)
    wait_after_visit_seconds: float = Field(default=0.0, nullable=False)
    total_rounds: int = Field(nullable=False)
    total_requested_kg: float = Field(nullable=False)
    total_planned_kg: float = Field(nullable=False)
    estimated_total_seconds: float = Field(nullable=False)
    cage_plans: list[dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False))
    created_by_id: Optional[UUID] = Field(default=None)
    created_by_name: Optional[str] = Field(default=None, max_length=100)
    last_run_on: Optional[str] = Field(default=None, max_length=10)
    last_session_id: Optional[str] = Field(default=None, max_length=36)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
