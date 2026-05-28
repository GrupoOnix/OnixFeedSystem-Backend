from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, Index
from sqlmodel import Field, SQLModel


class LastValidCyclicFeedingConfigModel(SQLModel, table=True):
    __tablename__ = "last_valid_cyclic_feeding_configs"
    __table_args__ = (Index("ix_last_valid_cyclic_feeding_configs_line_id", "line_id", unique=True),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    line_id: UUID = Field(
        foreign_key="feeding_lines.id",
        nullable=False,
        ondelete="CASCADE",
    )
    group_id: UUID = Field(nullable=False)
    doser_id: UUID = Field(nullable=False)
    visits: int = Field(nullable=False)
    blower_power_percentage: float = Field(nullable=False)
    wait_after_visit_seconds: float = Field(default=0.0, nullable=False)
    cage_configs: list[dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False))
    updated_by: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
