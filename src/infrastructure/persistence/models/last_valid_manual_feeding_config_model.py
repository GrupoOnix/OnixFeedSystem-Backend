from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index
from sqlmodel import Field, SQLModel


class LastValidManualFeedingConfigModel(SQLModel, table=True):
    __tablename__ = "last_valid_manual_feeding_configs"
    __table_args__ = (Index("ix_last_valid_manual_feeding_configs_line_id", "line_id", unique=True),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    line_id: UUID = Field(
        foreign_key="feeding_lines.id",
        nullable=False,
        ondelete="CASCADE",
    )
    target_silo_id: UUID = Field(nullable=False)
    target_cage_id: UUID = Field(nullable=False)
    target_amount_kg: float = Field(nullable=False)
    dosing_rate_kg_per_min: float = Field(nullable=False)
    dosing_unit: str = Field(nullable=False, max_length=50)
    blower_power_percentage: float = Field(nullable=False)
    updated_by: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
