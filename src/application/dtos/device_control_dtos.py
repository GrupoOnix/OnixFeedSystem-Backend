"""DTOs para control directo de devices."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SetBlowerPowerRequest(BaseModel):
    """Request para establecer la potencia del blower."""

    power_percentage: float = Field(..., ge=0.0, le=100.0, description="Potencia del blower (0-100%)")


class SetDoserRateRequest(BaseModel):
    """Request para establecer la tasa de dosificación."""

    rate_kg_min: float = Field(..., ge=0.0, description="Tasa de dosificación en kg/min")


class SetDoserSpeedRequest(BaseModel):
    """Request para establecer la velocidad del motor del dosificador."""

    speed_percentage: int = Field(..., ge=1, le=100, description="Velocidad del motor del dosificador (1-100%)")


class DoserCalibrationRequest(BaseModel):
    """Request para registrar una calibración del dosificador."""

    grams_per_second: float = Field(..., gt=0.0, description="Caudal calibrado en g/s")
    method: str = Field(..., min_length=1, max_length=50)
    sample_average_grams: Optional[float] = Field(default=None, gt=0.0)
    pulse_count: Optional[int] = Field(default=None, gt=0)
    active_time_seconds: Optional[float] = Field(default=None, gt=0.0)
    target_grams: Optional[float] = Field(default=None, gt=0.0)
    runtime_seconds: Optional[float] = Field(default=None, gt=0.0)
    created_by: Optional[str] = Field(default=None, max_length=100)


class DoserCalibrationResponse(BaseModel):
    id: str
    created_at: datetime
    grams_per_second: float
    method: str
    pulse_count: Optional[int] = None
    target_grams: Optional[float] = None
    runtime_seconds: Optional[float] = None
    sample_average_grams: Optional[float] = None
    active_time_seconds: Optional[float] = None
    created_by: Optional[str] = None


class RunDoserPulsesRequest(BaseModel):
    """Request para ejecutar pulsos controlados por backend."""

    pulse_count: int = Field(..., ge=1, le=100)


class RunDoserDurationRequest(BaseModel):
    """Request para ejecutar el dosificador por una duración acotada."""

    duration_seconds: float = Field(..., gt=0.0, le=300.0)


class StartCalibrationSessionRequest(BaseModel):
    """Inicia una sesión iterativa para un Pulse Doser."""

    target_grams: float = Field(..., gt=0.0, le=100000.0)
    tolerance_percentage: Optional[float] = Field(default=None, gt=0.0, le=100.0)


class StartCalibrationAttemptRequest(BaseModel):
    pulse_count: int = Field(..., ge=1, le=100)


class RecordCalibrationMeasurementRequest(BaseModel):
    measured_grams: float = Field(..., gt=0.0, le=100000.0)
    included: bool = True


class CalibrationMeasurementInput(RecordCalibrationMeasurementRequest):
    attempt_id: str


class RecordCalibrationMeasurementsRequest(BaseModel):
    measurements: list[CalibrationMeasurementInput] = Field(..., min_length=1)


class CalibrationAttemptResponse(BaseModel):
    id: str
    sequence: int
    status: str
    pulse_count: int
    active_time_seconds: float
    expected_grams: Optional[float] = None
    measured_grams: Optional[float] = None
    error_percentage: Optional[float] = None
    included: bool


class CalibrationSessionResponse(BaseModel):
    id: str
    doser_id: str
    line_id: str
    status: str
    target_grams: float
    pulse_on_time: float
    pulse_off_time: float
    speed_percentage: int
    tolerance_percentage: float
    final_grams_per_second: Optional[float] = None
    attempts: list[CalibrationAttemptResponse] = []


class SetCoolerPowerRequest(BaseModel):
    """Request para establecer la potencia del cooler."""

    power_percentage: float = Field(..., ge=0.0, le=100.0, description="Potencia del cooler (0-100%)")


class MoveSelectorRequest(BaseModel):
    """Request para mover el selector a un slot específico."""

    slot_number: int = Field(..., ge=1, description="Número de slot (1 a capacity)")


class BlowerStatusResponse(BaseModel):
    blower_id: str
    is_running: bool
    current_power: float


class DoserStatusResponse(BaseModel):
    doser_id: str
    is_running: bool
    current_rate_kg_min: float
    max_rate_kg_min: float
    calibrated_grams_per_second: Optional[float] = None


class SelectorStatusResponse(BaseModel):
    selector_id: str
    current_slot: Optional[int]


class CoolerStatusResponse(BaseModel):
    cooler_id: str
    is_on: bool
    current_power: float
