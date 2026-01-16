"""
Modelos Pydantic para las respuestas de API relacionadas con sensores.

Define la estructura de datos para exponer lecturas de sensores
a través de los endpoints REST.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class SensorReadingResponse(BaseModel):
    """Respuesta con una lectura individual de sensor."""

    model_config = ConfigDict(extra="forbid")

    sensor_id: str = Field(..., description="ID del sensor")
    sensor_type: str = Field(
        ..., description="Tipo de sensor (TEMPERATURE, PRESSURE, FLOW)"
    )
    value: float = Field(..., description="Valor medido por el sensor")
    unit: str = Field(..., description="Unidad de medida (°C, bar, m³/min)")
    timestamp: datetime = Field(..., description="Momento de la lectura")
    is_warning: bool = Field(
        default=False, description="Indica si el valor está en rango de advertencia"
    )
    is_critical: bool = Field(
        default=False, description="Indica si el valor está en rango crítico"
    )


class SensorReadingsResponse(BaseModel):
    """Respuesta con todas las lecturas de sensores de una línea."""

    model_config = ConfigDict(extra="forbid")

    line_id: str = Field(..., description="ID de la línea de alimentación")
    readings: List[SensorReadingResponse] = Field(
        ..., description="Lista de lecturas de sensores"
    )
    timestamp: datetime = Field(..., description="Timestamp de la consulta")
