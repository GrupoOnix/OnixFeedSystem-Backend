import uuid
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ManualFeedingRequest(BaseModel):

    line_id: str = Field(description="ID de la línea de alimentación (UUID)")
    cage_id: str = Field(description="ID de la jaula a alimentar (UUID)")
    doser_id: str = Field(description="ID del doser a usar (UUID)")
    quantity_kg: float = Field(gt=0, description="Cantidad a dispensar en kg")
    rate_kg_per_min: float = Field(gt=0, description="Tasa de alimentación en kg/min")
    blower_power_percentage: float = Field(ge=30, le=100, description="Potencia del blower en porcentaje (30-100%). Mínimo operativo: 30%.")
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
    power_percentage: float = Field(ge=30, le=100, description="Potencia del blower en porcentaje (30-100%). Mínimo operativo: 30%.")


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


class CageConfigInput(BaseModel):
    """Configuración de una jaula dentro de una alimentación cíclica."""

    cage_id: str = Field(description="ID de la jaula (UUID)")
    quantity_kg: float = Field(
        gt=0,
        description=(
            "Dosis objetivo en kg. En modo PAUSE se usa solo para calcular "
            "la duración de la visita simulada, no se dispensa ni descuenta stock."
        ),
    )
    rate_kg_per_min: float = Field(
        gt=0,
        description=(
            "Tasa en kg/min. En modo PAUSE se usa solo para calcular "
            "la duración de la visita simulada."
        ),
    )
    mode: str = Field(description="Modo de alimentación: 'NORMAL', 'PAUSE' o 'FASTING'")

    @field_validator("cage_id")
    @classmethod
    def validate_cage_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"'{v}' no es un UUID válido")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in ("NORMAL", "PAUSE", "FASTING"):
            raise ValueError("mode debe ser 'NORMAL', 'PAUSE' o 'FASTING'")
        return v


class CyclicFeedingRequest(BaseModel):
    """Request para iniciar una alimentación cíclica sobre un grupo de jaulas."""

    line_id: str = Field(description="ID de la línea de alimentación (UUID)")
    group_id: str = Field(description="ID del grupo de jaulas (UUID)")
    doser_id: str = Field(description="ID del doser a usar (UUID)")
    visits: int = Field(ge=1, description="Número de veces que la línea visitará cada jaula")
    blower_power_percentage: float = Field(
        ge=30, le=100, description="Potencia del blower en porcentaje (30-100%)"
    )
    operator_id: str = Field(description="ID del operador (UUID)")
    allow_overtime: bool = Field(
        default=False,
        description="Permitir que la alimentación se extienda más allá del horario operativo",
    )
    cage_configs: List[CageConfigInput] = Field(
        min_length=1,
        description="Configuración por jaula. Debe incluir todas las jaulas del grupo.",
    )

    @field_validator("line_id", "group_id", "doser_id", "operator_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"'{v}' no es un UUID válido")


class CyclicFeedingResponse(BaseModel):
    """Response para inicio de alimentación cíclica."""

    session_id: str = Field(description="ID de la sesión creada")
    cage_feeding_ids: List[str] = Field(description="IDs de los registros de alimentación por jaula")
    total_programmed_kg: float = Field(description="Total de kg a dispensar en toda la sesión")
    estimated_total_seconds: float = Field(description="Duración estimada total en segundos")
    estimated_total_minutes: float = Field(description="Duración estimada total en minutos")
    message: str = Field(description="Mensaje descriptivo de la operación")


class CageFeedingStatusItem(BaseModel):
    """Estado de alimentación de una jaula individual dentro de una sesión cíclica."""

    cage_id: str
    mode: str
    status: str
    execution_order: int
    programmed_kg: float
    dispensed_kg: float
    programmed_visits: int
    completed_visits: int
    visits_completion_percentage: float
    kg_completion_percentage: float


class CyclicSessionStatusResponse(BaseModel):
    """Estado completo de una sesión de alimentación cíclica."""

    session_id: str
    session_status: str
    line_id: str
    total_programmed_kg: float
    total_dispensed_kg: float
    total_rounds: int
    current_round: int
    # Estado de la jaula siendo visitada actualmente (None si no hay visita activa)
    active_cage_id: Optional[str]
    dispensed_kg_live: float
    current_stage: str
    is_running: bool
    is_paused: bool
    current_flow_rate_kg_per_min: float
    # Detalle por jaula
    cages: List[CageFeedingStatusItem]
