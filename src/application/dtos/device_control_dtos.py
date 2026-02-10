"""DTOs para control directo de devices."""

from pydantic import BaseModel, Field


class SetBlowerPowerRequest(BaseModel):
    """Request para establecer la potencia del blower."""

    power_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Potencia del blower (0-100%)"
    )


class SetDoserRateRequest(BaseModel):
    """Request para establecer la tasa de dosificación."""

    rate_kg_min: float = Field(
        ..., ge=0.0, description="Tasa de dosificación en kg/min"
    )


class SetDoserSpeedRequest(BaseModel):
    """Request para establecer la velocidad del motor del dosificador."""

    speed_percentage: int = Field(
        ..., ge=1, le=100, description="Velocidad del motor del dosificador (1-100%)"
    )


class MoveSelectorRequest(BaseModel):
    """Request para mover el selector a un slot específico."""

    slot_number: int = Field(..., ge=1, description="Número de slot (1 a capacity)")
