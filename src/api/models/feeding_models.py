import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ManualFeedingRequest(BaseModel):
    line_id: str = Field(description="ID de la línea de alimentación (UUID)")
    cage_id: str = Field(description="ID de la jaula a alimentar (UUID)")
    doser_id: str = Field(description="ID del doser a usar (UUID)")
    silo_id: str = Field(description="ID del silo a usar (UUID)")
    quantity_kg: float = Field(gt=0, description="Cantidad a dispensar en kg")
    rate_kg_per_min: float = Field(gt=0, description="Tasa de alimentación en kg/min")
    blower_power_percentage: float = Field(
        ge=30,
        le=100,
        description="Potencia del blower en porcentaje (30-100%). Mínimo operativo: 30%.",
    )
    allow_overtime: bool = Field(
        default=False, description="Permitir que la alimentación se extienda más allá del horario operativo"
    )

    @field_validator("line_id", "cage_id", "doser_id", "silo_id")
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
                    "allow_overtime": False,
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
                    "message": "Alimentación manual iniciada exitosamente",
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


class UpdateAmountRequest(BaseModel):
    amount_kg: float = Field(gt=0, description="Nueva cantidad objetivo en kg")


class UpdateAmountResponse(BaseModel):
    message: str
    new_amount_kg: float


class UpdateCageModeRequest(BaseModel):
    mode: str = Field(description="Nuevo modo para próximas visitas: 'NORMAL' o 'PAUSE'")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in ("NORMAL", "PAUSE"):
            raise ValueError("mode debe ser 'NORMAL' o 'PAUSE'")
        return v


class UpdateCageModeResponse(BaseModel):
    message: str
    cage_id: str
    previous_mode: str
    new_mode: str
    applied_immediately: bool


class PauseFeedingRequest(BaseModel):
    reason: str = Field(description="Motivo de la pausa")


class ResumeFeedingRequest(BaseModel):
    pass


class CancelFeedingRequest(BaseModel):
    reason: str = Field(description="Motivo de la cancelación")


class UpdateBlowerRequest(BaseModel):
    power_percentage: float = Field(
        ge=30,
        le=100,
        description="Potencia del blower en porcentaje (30-100%). Mínimo operativo: 30%.",
    )


class UpdateBlowerResponse(BaseModel):
    message: str
    power_percentage: float


class FeedingSessionStatusResponse(BaseModel):
    session_id: str
    session_status: str
    line_id: str
    started_at: datetime
    cage_id: str
    cage_name: str
    programmed_kg: float
    dispensed_kg_bd: float
    dispensed_kg_live: float
    rate_kg_per_min: float
    current_flow_rate_kg_per_min: float
    is_running: bool
    is_paused: bool
    completion_percentage: float
    current_stage: str
    server_timestamp: datetime


class CageConfigInput(BaseModel):
    """Configuración de una jaula dentro de una alimentación cíclica."""

    cage_id: str = Field(description="ID de la jaula (UUID)")
    visits: Optional[int] = Field(
        default=None,
        ge=1,
        description=(
            "Número de visitas para esta jaula. Si se omite, se usa el valor global "
            "deprecated de CyclicFeedingRequest.visits."
        ),
    )
    quantity_kg: float = Field(
        ge=0,
        description=(
            "Cantidad TOTAL de alimento para esta jaula (se dividirá automáticamente entre las visitas). "
            "En modo PAUSE se usa solo para calcular la duración de las visitas simuladas, "
            "no se dispensa ni descuenta stock. "
            "En modo FASTING se ignora (puede enviarse 0)."
        ),
    )
    rate_kg_per_min: float = Field(
        ge=0,
        description=(
            "Tasa en kg/min. En modo PAUSE se usa solo para calcular "
            "la duración de la visita simulada. "
            "En modo FASTING se ignora (puede enviarse 0)."
        ),
    )
    mode: str = Field(description="Modo de alimentación: 'NORMAL', 'PAUSE' o 'FASTING'")
    visit_quantities_kg: Optional[List[float]] = Field(
        default=None,
        description="Plan opcional por ronda. Permite visitas vacías y cantidades distintas.",
    )

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

    @model_validator(mode="after")
    def validate_quantities_by_mode(self) -> "CageConfigInput":
        if self.mode == "NORMAL":
            if self.quantity_kg <= 0:
                raise ValueError(f"quantity_kg debe ser > 0 para el modo '{self.mode}'")
            if self.rate_kg_per_min <= 0:
                raise ValueError(f"rate_kg_per_min debe ser > 0 para el modo '{self.mode}'")
        if self.mode != "FASTING":
            if self.visit_quantities_kg is not None:
                if any(quantity < 0 for quantity in self.visit_quantities_kg):
                    raise ValueError("visit_quantities_kg no puede contener valores negativos")
                if self.visits is not None and len(self.visit_quantities_kg) != self.visits:
                    raise ValueError("visit_quantities_kg debe tener una entrada por visita")
                if round(sum(self.visit_quantities_kg), 6) != round(self.quantity_kg, 6):
                    raise ValueError("visit_quantities_kg debe sumar quantity_kg")
        return self


class CyclicFeedingRequest(BaseModel):
    """Request para iniciar una alimentación cíclica sobre un grupo de jaulas."""

    line_id: str = Field(description="ID de la línea de alimentación (UUID)")
    group_id: str = Field(description="ID del grupo de jaulas (UUID)")
    doser_id: str = Field(description="ID del doser a usar (UUID)")
    silo_id: str = Field(description="ID del silo a usar (UUID)")
    visits: Optional[int] = Field(
        default=None,
        ge=1,
        description=(
            "Número global de visitas por jaula (deprecated). Se usa como fallback "
            "si una jaula no declara cage_configs[].visits."
        ),
    )
    blower_power_percentage: float = Field(ge=30, le=100, description="Potencia del blower en porcentaje (30-100%)")
    wait_after_visit_seconds: float = Field(
        default=0,
        ge=0,
        description="Tiempo de espera en segundos después de cada visita cíclica, excepto la última.",
    )
    allow_overtime: bool = Field(
        default=False,
        description="Permitir que la alimentación se extienda más allá del horario operativo",
    )
    cage_configs: List[CageConfigInput] = Field(
        min_length=1,
        description="Configuración por jaula. Debe incluir todas las jaulas del grupo.",
    )

    @field_validator("line_id", "group_id", "doser_id", "silo_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"'{v}' no es un UUID válido")

    @model_validator(mode="after")
    def validate_visits_fallback(self) -> "CyclicFeedingRequest":
        for cage_config in self.cage_configs:
            if cage_config.mode != "FASTING" and cage_config.visits is None and self.visits is None:
                raise ValueError("Cada jaula activa debe declarar visits o el request debe incluir visits global")
        return self


class ScheduledPlanCageInput(BaseModel):
    """Meta diaria de una jaula usada para calcular una programación."""

    cage_id: str
    daily_target_kg: float = Field(ge=0)
    mode: str = "NORMAL"

    @field_validator("cage_id")
    @classmethod
    def validate_uuid(cls, value: str) -> str:
        try:
            uuid.UUID(value)
        except ValueError as exc:
            raise ValueError(f"'{value}' no es un UUID válido") from exc
        return value

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        if value not in ("NORMAL", "PAUSE", "FASTING"):
            raise ValueError("mode debe ser 'NORMAL', 'PAUSE' o 'FASTING'")
        return value


class ScheduledFeedingPlanRequest(BaseModel):
    """Datos necesarios para calcular y guardar un plan diario."""

    name: str = Field(min_length=1, max_length=120)
    line_id: str
    group_id: str
    doser_id: str
    silo_id: str
    start_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: str = Field(default="America/Santiago", max_length=64)
    blower_power_percentage: float = Field(default=70, ge=30, le=100)
    wait_after_visit_seconds: float = Field(default=0, ge=0)
    is_active: bool = True
    cage_configs: List[ScheduledPlanCageInput] = Field(min_length=1)

    @field_validator("line_id", "group_id", "doser_id", "silo_id")
    @classmethod
    def validate_uuid(cls, value: str) -> str:
        try:
            uuid.UUID(value)
        except ValueError as exc:
            raise ValueError(f"'{value}' no es un UUID válido") from exc
        return value


class ScheduledPlanCageResponse(BaseModel):
    cage_id: str
    cage_name: str
    mode: str
    rate_kg_per_min: float
    requested_kg: float
    grams_per_pulse: float | None
    planned_pulses: int
    planned_kg: float
    rounding_excess_kg: float
    pulse_schedule: List[int]
    quantity_schedule_kg: List[float]


class ScheduledFeedingPlanResponse(BaseModel):
    id: Optional[str] = None
    name: str
    line_id: str
    group_id: str
    doser_id: str
    silo_id: str
    start_time: str
    end_time: str
    timezone: str
    blower_power_percentage: float
    wait_after_visit_seconds: float
    is_active: bool
    total_rounds: int
    total_requested_kg: float
    total_planned_kg: float
    rounding_excess_kg: float
    estimated_total_seconds: float
    window_seconds: float
    remaining_seconds: float
    cage_plans: List[ScheduledPlanCageResponse]
    last_run_on: Optional[str] = None
    last_session_id: Optional[str] = None
    last_error: Optional[str] = None


class ToggleScheduledFeedingPlanRequest(BaseModel):
    is_active: bool


class CyclicFeedingResponse(BaseModel):
    """Response para inicio de alimentación cíclica."""

    session_id: str = Field(description="ID de la sesión creada")
    cage_feeding_ids: List[str] = Field(description="IDs de los registros de alimentación por jaula")
    total_programmed_kg: float = Field(description="Total de kg a dispensar en toda la sesión")
    estimated_total_seconds: float = Field(description="Duración estimada total en segundos")
    estimated_total_minutes: float = Field(description="Duración estimada total en minutos")
    message: str = Field(description="Mensaje descriptivo de la operación")


class CageSummaryItem(BaseModel):
    cage_id: str
    cage_name: str
    mode: str
    status: str
    execution_order: int
    programmed_kg_per_visit: float
    total_programmed_kg: float
    total_dispensed_kg: float
    programmed_visits: int
    completed_visits: int
    overall_completion_percentage: float
    grams_per_pulse: Optional[float] = None
    pulses_per_visit: Optional[int] = None
    estimated_pulses_total: Optional[int] = None


class ActiveCageInfo(BaseModel):
    cage_id: str
    cage_name: str
    execution_order: int
    total_cages: int
    current_visit_number: int
    total_visits: int
    current_stage: str
    is_empty_visit: bool = False
    current_visit_dispensed_kg: float
    current_visit_programmed_kg: float
    programmed_kg_per_visit: float
    current_visit_completion_percentage: float
    current_flow_rate_kg_per_min: float
    grams_per_pulse: Optional[float] = None
    pulses_per_visit: Optional[int] = None
    estimated_pulses_total: Optional[int] = None


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
    started_at: datetime
    total_programmed_kg: float
    total_dispensed_kg: float
    overall_completion_percentage: float
    total_rounds: int
    current_round: int
    active_cage: Optional[ActiveCageInfo]
    cages_summary: List[CageSummaryItem]
    server_timestamp: datetime


class ActiveSessionItem(BaseModel):
    session_id: str
    line_id: str
    type: str
    status: str
    started_at: datetime


class BatchStatusSessionManual(BaseModel):
    session_id: str
    line_id: str
    type: str
    status: str
    started_at: datetime
    cage_id: str
    cage_name: str
    programmed_kg: float
    dispensed_kg_bd: float
    dispensed_kg_live: float
    current_flow_rate_kg_per_min: float
    is_running: bool
    is_paused: bool
    completion_percentage: float
    current_stage: str
    server_timestamp: datetime


class BatchStatusSessionCyclic(BaseModel):
    session_id: str
    line_id: str
    type: str
    status: str
    started_at: datetime
    total_programmed_kg: float
    total_dispensed_kg: float
    overall_completion_percentage: float
    current_round: int
    total_rounds: int
    active_cage: Optional[ActiveCageInfo]
    cages_summary: List[CageSummaryItem]
    server_timestamp: datetime


class BatchStatusResponse(BaseModel):
    sessions: List[Any]
    server_timestamp: datetime


class SessionHistoryItem(BaseModel):
    session_id: str
    type: str
    status: str
    line_id: str
    line_name: str
    operator_id: Optional[str] = None
    operator_name: Optional[str] = None
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: Optional[float]
    total_programmed_kg: float
    total_dispensed_kg: float


class CageHistorySummary(BaseModel):
    cage_id: str
    cage_name: str
    mode: str
    programmed_kg: float
    total_dispensed_kg: float
    programmed_visits: int
    completed_visits: int
    avg_visit_duration_seconds: Optional[float]


class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]


class RateChartPoint(BaseModel):
    timestamp: datetime
    rate_kg_per_min: float


class BatchConsumptionItem(BaseModel):
    id: str
    cage_feeding_id: str
    silo_id: str
    batch_id: str
    food_id: str
    food_name: str
    food_code: str
    food_provider: str
    quantity_kg: float
    operator_id: str
    created_at: datetime


class SessionHistoryDetail(BaseModel):
    session_id: str
    type: str
    status: str
    line_id: str
    line_name: str
    operator_id: Optional[str] = None
    operator_name: Optional[str] = None
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: Optional[float]
    total_programmed_kg: float
    total_dispensed_kg: float
    cages: List[CageHistorySummary]
    timeline: List[TimelineEvent]
    rate_chart: List[RateChartPoint]
    batch_consumptions: List[BatchConsumptionItem] = Field(default_factory=list)


class VisitHistoryItem(BaseModel):
    visit_number: int
    dispensed_kg: float
    dispensed_grams: float
    duration_seconds: float
    completed_at: datetime
    is_empty_visit: bool = False


class CageVisitHistory(BaseModel):
    session_id: str
    cage_id: str
    cage_name: str
    visits: List[VisitHistoryItem]
    total_dispensed_kg: float
    avg_duration_seconds: Optional[float]


class DailyFeedingStatsResponse(BaseModel):
    date: str
    total_dispensed_kg: float
    total_programmed_kg: float
    sessions_completed: int
    sessions_in_progress: int


class DailyFeedingSummaryPoint(BaseModel):
    date: str
    total_dispensed_kg: float
    total_programmed_kg: float
    sessions_completed: int
    sessions_cancelled: int
    sessions_interrupted: int


class DailyFeedingSummaryResponse(BaseModel):
    start_date: str
    end_date: str
    points: List[DailyFeedingSummaryPoint]


class RateTimelineSummary(BaseModel):
    total_dispensed_kg: float
    active_minutes: int
    avg_active_rate_kg_per_min: float
    peak_total_rate_kg_per_min: float
    peak_total_rate_at: Optional[datetime]
    max_overlapping_sessions: int


class TotalRateTimelinePoint(BaseModel):
    timestamp: datetime
    rate_kg_per_min: float
    active_sessions: int


class RateTimelinePoint(BaseModel):
    timestamp: datetime
    rate_kg_per_min: float
    dispensed_kg: float
    active_sessions: int


class RateTimelineSeries(BaseModel):
    id: str
    name: str
    kind: str
    color_hint: str
    points: List[RateTimelinePoint]


class FeedingRateTimelineResponse(BaseModel):
    start_at: datetime
    end_at: datetime
    bucket_seconds: int
    timezone: str
    summary: RateTimelineSummary
    total_series: List[TotalRateTimelinePoint]
    series: List[RateTimelineSeries]
