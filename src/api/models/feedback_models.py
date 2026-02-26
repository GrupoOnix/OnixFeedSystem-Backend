"""Modelos de request/response para el endpoint de Feedback."""

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class CreateFeedbackRequestModel(BaseModel):
    """Modelo de request para crear un feedback."""

    name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Nombre del usuario (opcional)",
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Email del usuario (opcional)",
    )
    type: Literal["suggestion", "bug", "general"] = Field(
        ...,
        description="Tipo de feedback: 'suggestion', 'bug' o 'general'",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Mensaje de feedback",
    )
