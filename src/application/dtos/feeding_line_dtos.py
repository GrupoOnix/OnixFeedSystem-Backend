from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class BlowerDTO:
    """DTO para representar un blower."""

    id: str
    name: str
    non_feeding_power: float
    current_power: float
    blow_before_feeding_time: int
    blow_after_feeding_time: int


@dataclass
class DoserDTO:
    """DTO para representar un dosificador."""

    id: str
    name: str
    doser_type: str
    current_rate: float
    dosing_range_min: float
    dosing_range_max: float
    speed_percentage: int = 50
    silo_id: Optional[str] = None
    silo_name: Optional[str] = None


@dataclass
class SelectorDTO:
    """DTO para representar un selector."""

    id: str
    name: str
    capacity: int
    fast_speed: float
    slow_speed: float
    current_slot: Optional[int] = None


@dataclass
class SensorDTO:
    """DTO para representar un sensor."""

    id: str
    name: str
    sensor_type: str


@dataclass
class FeedingLineDTO:
    """DTO para representar una línea de alimentación en respuestas de API."""

    id: str
    name: str
    created_at: datetime
    blower: BlowerDTO
    dosers: List[DoserDTO]
    selector: SelectorDTO
    sensors: List[SensorDTO]
    total_cages: int = 0


@dataclass
class ListFeedingLinesResponse:
    """Response con lista de líneas de alimentación."""

    feeding_lines: List[FeedingLineDTO]


# ============================================================================
# Request DTOs para actualización de componentes
# ============================================================================


@dataclass
class UpdateDoserRequest:
    """Request para actualizar la configuración de un doser."""

    name: Optional[str] = None
    assigned_silo_id: Optional[str] = None
    current_rate: Optional[float] = None
    dosing_range_min: Optional[float] = None
    dosing_range_max: Optional[float] = None
    speed_percentage: Optional[int] = None

    def __post_init__(self):
        """Validaciones del request."""
        if self.speed_percentage is not None and not (1 <= self.speed_percentage <= 100):
            raise ValueError("speed_percentage debe estar entre 1 y 100")
        if self.current_rate is not None and self.current_rate < 0:
            raise ValueError("current_rate debe ser mayor o igual a 0")
        if self.dosing_range_min is not None and self.dosing_range_min < 0:
            raise ValueError("dosing_range_min debe ser mayor o igual a 0")
        if self.dosing_range_max is not None and self.dosing_range_max < 0:
            raise ValueError("dosing_range_max debe ser mayor o igual a 0")
        if (
            self.dosing_range_min is not None
            and self.dosing_range_max is not None
            and self.dosing_range_min > self.dosing_range_max
        ):
            raise ValueError("dosing_range_min no puede ser mayor que dosing_range_max")


@dataclass
class UpdateBlowerRequest:
    """Request para actualizar la configuración de un blower."""

    name: Optional[str] = None
    non_feeding_power: Optional[float] = None
    current_power: Optional[float] = None
    blow_before_feeding_time: Optional[int] = None
    blow_after_feeding_time: Optional[int] = None

    def __post_init__(self):
        """Validaciones del request."""
        if self.non_feeding_power is not None and not (
            0 <= self.non_feeding_power <= 100
        ):
            raise ValueError("non_feeding_power debe estar entre 0 y 100")
        if self.current_power is not None and not (0 <= self.current_power <= 100):
            raise ValueError("current_power debe estar entre 0 y 100")
        if (
            self.blow_before_feeding_time is not None
            and self.blow_before_feeding_time < 0
        ):
            raise ValueError("blow_before_feeding_time debe ser mayor o igual a 0")
        if (
            self.blow_after_feeding_time is not None
            and self.blow_after_feeding_time < 0
        ):
            raise ValueError("blow_after_feeding_time debe ser mayor o igual a 0")


@dataclass
class UpdateSelectorRequest:
    """Request para actualizar la configuración de un selector."""

    name: Optional[str] = None
    fast_speed: Optional[float] = None
    slow_speed: Optional[float] = None
    current_slot: Optional[int] = None

    def __post_init__(self):
        """Validaciones del request."""
        if self.fast_speed is not None and not (0 <= self.fast_speed <= 100):
            raise ValueError("fast_speed debe estar entre 0 y 100")
        if self.slow_speed is not None and not (0 <= self.slow_speed <= 100):
            raise ValueError("slow_speed debe estar entre 0 y 100")
        if (
            self.fast_speed is not None
            and self.slow_speed is not None
            and self.slow_speed > self.fast_speed
        ):
            raise ValueError("slow_speed no puede ser mayor que fast_speed")
        # current_slot validation is done by the domain entity
