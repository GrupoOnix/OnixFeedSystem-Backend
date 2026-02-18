import uuid

from pydantic import BaseModel, Field, field_validator


class SystemConfigResponse(BaseModel):
    feeding_start_time: str = Field(description="Inicio del horario operativo (HH:MM)")
    feeding_end_time: str = Field(description="Fin del horario operativo (HH:MM)")
    timezone_id: str = Field(description="Identificador de timezone (ej. America/Santiago)")


class UpdateSystemConfigRequest(BaseModel):
    feeding_start_time: str = Field(description="Inicio del horario operativo (HH:MM)")
    feeding_end_time: str = Field(description="Fin del horario operativo (HH:MM)")
    timezone_id: str = Field(description="Identificador de timezone (ej. America/Santiago)")

    @field_validator("feeding_start_time", "feeding_end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError(f"'{v}' no tiene formato HH:MM")
        hour, minute = parts
        if not hour.isdigit() or not minute.isdigit():
            raise ValueError(f"'{v}' no tiene formato HH:MM")
        h, m = int(hour), int(minute)
        if not (0 <= h <= 23) or not (0 <= m <= 59):
            raise ValueError(f"'{v}' tiene valores fuera de rango")
        return v

    model_config = {"json_schema_extra": {"example": {
        "feeding_start_time": "06:00",
        "feeding_end_time": "18:00",
        "timezone_id": "America/Santiago",
    }}}


class ScheduleCheckRequest(BaseModel):
    line_id: str = Field(description="ID de la línea de alimentación (UUID)")
    cage_id: str = Field(description="ID de la jaula (UUID)")
    quantity_kg: float = Field(gt=0, description="Cantidad a dispensar en kg")
    rate_kg_per_min: float = Field(gt=0, description="Tasa de alimentación en kg/min")

    @field_validator("line_id", "cage_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"'{v}' no es un UUID válido")

    model_config = {"json_schema_extra": {"example": {
        "line_id": "123e4567-e89b-12d3-a456-426614174000",
        "cage_id": "123e4567-e89b-12d3-a456-426614174001",
        "quantity_kg": 50.0,
        "rate_kg_per_min": 5.0,
    }}}


class ScheduleCheckResponse(BaseModel):
    fits: bool = Field(description="True si la operación cabe dentro del horario operativo")
    estimated_seconds: float = Field(description="Duración estimada de la operación en segundos")
    estimated_minutes: float = Field(description="Duración estimada de la operación en minutos")
    remaining_seconds: float = Field(description="Segundos restantes en el horario operativo (0 si está fuera del horario)")
    remaining_minutes: float = Field(description="Minutos restantes en el horario operativo (0 si está fuera del horario)")
