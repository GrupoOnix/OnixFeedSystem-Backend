import uuid
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ManualFeedingRequest(BaseModel):

    line_id: str = Field(description="ID de la línea de alimentación (UUID)")
    cage_id: str = Field(description="ID de la jaula a alimentar (UUID)")
    doser_id: str = Field(description="ID del doser a usar (UUID)")
    quantity_kg: float = Field(gt=0, description="Cantidad a dispensar en kg")
    rate_kg_per_min: float = Field(gt=0, description="Tasa de alimentación en kg/min")
    blower_power_percentage: float = Field(ge=0, le=100, description="Potencia del blower en porcentaje (0-100)")
    operator_id: str = Field(description="ID del operador que inicia la alimentación (UUID)")
    allow_overtime: bool = Field(
        default=False,
        description="Permitir que la alimentación se extienda más allá del horario operativo"
    )

    @field_validator('line_id', 'cage_id', 'doser_id', 'operator_id')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"'{v}' no es un UUID válido")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "line_id": "123e4567-e89b-12d3-a456-426614174000",
                    "cage_id": "123e4567-e89b-12d3-a456-426614174001",
                    "quantity_kg": 50.0,
                    "rate_kg_per_min": 5.0,
                    "operator_id": "123e4567-e89b-12d3-a456-426614174002",
                    "allow_overtime": False
                }
            ]
        }
    }


class ManualFeedingResponse(BaseModel):
    """Response para inicio de alimentación manual."""

    session_id: str = Field(description="ID de la sesión de alimentación creada")
    cage_feeding_id: str = Field(description="ID del registro de alimentación de la jaula")
    estimated_duration_seconds: float = Field(description="Duración estimada en segundos")
    message: str = Field(description="Mensaje descriptivo de la operación")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
                    "cage_feeding_id": "123e4567-e89b-12d3-a456-426614174001",
                    "estimated_duration_seconds": 600.0,
                    "message": "Alimentación manual iniciada exitosamente"
                }
            ]
        }
    }


class FeedingActionResponse(BaseModel):
    message: str = Field(description="Mensaje descriptivo de la operación")


class UpdateRateRequest(BaseModel):
    rate_kg_per_min: float = Field(gt=0, description="Nueva tasa de alimentación en kg/min")


class UpdateRateResponse(BaseModel):
    message: str
    new_rate_kg_per_min: float


class PauseFeedingRequest(BaseModel):
    operator_id: str = Field(description="ID del operador (UUID)")
    reason: str = Field(description="Motivo de la pausa")

    @field_validator('operator_id')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"'{v}' no es un UUID válido")


class ResumeFeedingRequest(BaseModel):
    operator_id: str = Field(description="ID del operador (UUID)")

    @field_validator('operator_id')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"'{v}' no es un UUID válido")


class CancelFeedingRequest(BaseModel):
    operator_id: str = Field(description="ID del operador (UUID)")
    reason: str = Field(description="Motivo de la cancelación")

    @field_validator('operator_id')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"'{v}' no es un UUID válido")


class UpdateBlowerRequest(BaseModel):
    power_percentage: float = Field(ge=0, le=100, description="Potencia del blower en porcentaje (0-100)")


class UpdateBlowerResponse(BaseModel):
    message: str
    power_percentage: float


class FeedingSessionStatusResponse(BaseModel):
    session_id: str
    session_status: str
    line_id: str
    cage_id: str
    programmed_kg: float
    dispensed_kg_bd: float
    dispensed_kg_live: float
    rate_kg_per_min: float
    current_flow_rate_kg_per_min: float
    is_running: bool
    is_paused: bool
    completion_percentage: float
    current_stage: str
