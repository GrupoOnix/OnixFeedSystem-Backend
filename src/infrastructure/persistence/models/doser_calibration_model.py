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
    sample_average_grams: Optional[float] = Field(default=None)
    pulse_count: Optional[int] = Field(default=None)
    active_time_seconds: Optional[float] = Field(default=None)
    target_grams: Optional[float] = Field(default=None)
    runtime_seconds: Optional[float] = Field(default=None)
    created_by: Optional[str] = Field(default=None, max_length=100)
