"""Modelo durable para ejecuciones de alimentación en segundo plano."""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class FeedingExecutionJobModel(SQLModel, table=True):
    """Trabajo persistido que delega una sesión al orquestador."""

    __tablename__ = "feeding_execution_jobs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    feeding_session_id: str = Field(
        foreign_key="feeding_sessions.id",
        nullable=False,
        index=True,
        unique=True,
        ondelete="CASCADE",
    )
    status: str = Field(default="PENDING", max_length=20, nullable=False, index=True)
    payload: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    worker_id: Optional[str] = Field(default=None, max_length=255, index=True)
    attempts: int = Field(default=0, nullable=False)
    last_error: Optional[str] = Field(default=None, max_length=1000)
    heartbeat_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    lease_expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True, index=True),
    )
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
