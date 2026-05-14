from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index
from sqlmodel import Field, SQLModel


class LastSelectedFeedingModeModel(SQLModel, table=True):
    __tablename__ = "last_selected_feeding_modes"
    __table_args__ = (Index("ix_last_selected_feeding_modes_line_id", "line_id", unique=True),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    line_id: UUID = Field(
        foreign_key="feeding_lines.id",
        nullable=False,
        ondelete="CASCADE",
    )
    selected_mode: str = Field(nullable=False, max_length=20)
    updated_by: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
