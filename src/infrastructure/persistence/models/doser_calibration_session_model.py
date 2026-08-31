"""Sesiones e intentos durables de calibración de Pulse Dosers."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class DoserCalibrationSessionModel(SQLModel, table=True):
    __tablename__ = "doser_calibration_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    doser_id: UUID = Field(foreign_key="dosers.id", nullable=False, index=True, ondelete="CASCADE")
    line_id: UUID = Field(foreign_key="feeding_lines.id", nullable=False, index=True, ondelete="CASCADE")
    status: str = Field(default="PENDING", max_length=32, nullable=False, index=True)
    target_grams: float = Field(gt=0, nullable=False)
    pulse_on_time: float = Field(gt=0, nullable=False)
    pulse_off_time: float = Field(ge=0, nullable=False)
    speed_percentage: int = Field(ge=1, le=100, nullable=False)
    tolerance_percentage: float = Field(gt=0, nullable=False)
    food_id: Optional[UUID] = Field(default=None, foreign_key="foods.id", ondelete="SET NULL")
    started_by: str = Field(max_length=100, nullable=False)
    heartbeat_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    final_calibration_id: Optional[UUID] = Field(default=None, foreign_key="doser_calibrations.id", ondelete="SET NULL")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )


class DoserCalibrationAttemptModel(SQLModel, table=True):
    __tablename__ = "doser_calibration_attempts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(
        foreign_key="doser_calibration_sessions.id", nullable=False, index=True, ondelete="CASCADE"
    )
    sequence: int = Field(ge=1, nullable=False)
    status: str = Field(default="PENDING", max_length=32, nullable=False, index=True)
    pulse_count: int = Field(ge=1, nullable=False)
    active_time_seconds: float = Field(gt=0, nullable=False)
    expected_grams: Optional[float] = Field(default=None)
    measured_grams: Optional[float] = Field(default=None)
    error_percentage: Optional[float] = Field(default=None)
    included: bool = Field(default=True, nullable=False)
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False)
    )
