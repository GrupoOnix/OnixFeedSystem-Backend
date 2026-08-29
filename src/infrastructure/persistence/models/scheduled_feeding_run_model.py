"""Registro durable de cada disparo diario de un plan programado."""

from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


class ScheduledFeedingRunModel(SQLModel, table=True):
    __tablename__ = "scheduled_feeding_runs"
    __table_args__ = (UniqueConstraint("plan_id", "run_date", name="uq_scheduled_feeding_runs_plan_date"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    plan_id: UUID = Field(foreign_key="scheduled_feeding_plans.id", nullable=False, index=True, ondelete="CASCADE")
    run_date: date = Field(nullable=False, index=True)
    status: str = Field(default="CLAIMED", max_length=20, nullable=False, index=True)
    worker_id: Optional[str] = Field(default=None, max_length=255)
    attempts: int = Field(default=1, nullable=False)
    lease_expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True, index=True),
    )
    session_id: Optional[str] = Field(default=None, max_length=36, index=True)
    error: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
