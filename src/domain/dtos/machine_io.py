from dataclasses import dataclass
from enum import Enum
from typing import Optional


class VisitStage(str, Enum):
    IDLE = "IDLE"
    POSITIONING_SELECTOR = "POSITIONING_SELECTOR"
    BLOWING_BEFORE = "BLOWING_BEFORE"
    FEEDING = "FEEDING"
    BLOWING_AFTER = "BLOWING_AFTER"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True)
class MachineCommand:
    slot_number: int
    target_kg: float
    doser_rate_kg_per_min: float
    blower_power_percentage: float
    transport_time_seconds: float
    blow_before_seconds: float
    blow_after_seconds: float
    selector_positioning_seconds: float = 5.0

    def __post_init__(self):
        if self.slot_number < 0:
            raise ValueError("slot_number no puede ser negativo")
        if self.target_kg <= 0:
            raise ValueError("target_kg debe ser mayor a 0")
        if self.doser_rate_kg_per_min <= 0:
            raise ValueError("doser_rate_kg_per_min debe ser mayor a 0")
        if not (0.0 <= self.blower_power_percentage <= 100.0):
            raise ValueError("blower_power_percentage debe estar entre 0 y 100")


@dataclass(frozen=True)
class MachineVisitStatus:
    is_running: bool
    is_paused: bool
    dispensed_kg: float
    current_flow_rate_kg_per_min: float
    has_error: bool
    current_stage: VisitStage = VisitStage.POSITIONING_SELECTOR
    error_code: Optional[int] = None
