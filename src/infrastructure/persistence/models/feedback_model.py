from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from domain.aggregates.feedback import Feedback


class FeedbackModel(SQLModel, table=True):
    """Modelo de persistencia para Feedback."""

    __tablename__ = "feedback"

    id: UUID = Field(primary_key=True)
    name: Optional[str] = Field(default=None, max_length=200)
    email: Optional[str] = Field(default=None, max_length=200)
    type: str = Field(max_length=20)
    message: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    user_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True),
    )

    @staticmethod
    def from_domain(feedback: Feedback) -> "FeedbackModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return FeedbackModel(
            id=feedback.id,
            name=feedback.name,
            email=feedback.email,
            type=feedback.type,
            message=feedback.message,
            created_at=feedback.created_at,
            user_id=feedback.user_id.value if hasattr(feedback, "user_id") and feedback.user_id else None,
        )
