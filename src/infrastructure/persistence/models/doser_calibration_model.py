from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class DoserCalibrationModel(SQLModel, table=True):
    __tablename__ = "doser_calibrations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    doser_id: UUID = Field(foreign_key="dosers.id", index=True, ondelete="CASCADE")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    grams_per_second: float
    method: str
    status: str = Field(default="VERIFIED", max_length=32, nullable=False, index=True)
    food_id: Optional[UUID] = Field(default=None, foreign_key="foods.id", ondelete="SET NULL")
    speed_percentage: Optional[int] = Field(default=None)
    pulse_on_time: Optional[float] = Field(default=None)
    pulse_off_time: Optional[float] = Field(default=None)
    tolerance_percentage: Optional[float] = Field(default=None)
    included_attempts: int = Field(default=1, nullable=False)
    restored_from_id: Optional[UUID] = Field(default=None, foreign_key="doser_calibrations.id", ondelete="SET NULL")
    sample_average_grams: Optional[float] = Field(default=None)
    pulse_count: Optional[int] = Field(default=None)
    active_time_seconds: Optional[float] = Field(default=None)
    target_grams: Optional[float] = Field(default=None)
    runtime_seconds: Optional[float] = Field(default=None)
    created_by: Optional[str] = Field(default=None, max_length=100)
