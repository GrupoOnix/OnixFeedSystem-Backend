from dataclasses import dataclass
from typing import List, Optional
from domain.enums import FeedingMode

@dataclass(frozen=True)
class MachineConfiguration:
    start_command: bool
    mode: FeedingMode
    slot_numbers: List[int]
    blower_speed_percentage: float
    doser_speed_percentage: float
    target_amount_kg: float
    batch_amount_kg: float = 0.0
    pause_time_seconds: int = 0

    def __post_init__(self):
        if not self.slot_numbers:
            raise ValueError("La configuración debe tener al menos un slot objetivo.")

@dataclass(frozen=True)
class MachineStatus:
    is_running: bool
    is_paused: bool
    current_mode: FeedingMode
    total_dispensed_kg: float
    current_flow_rate: float
    current_slot_number: int
    current_list_index: int
    current_cycle_index: int
    total_cycles_configured: int
    has_error: bool = False
    error_code: Optional[int] = None
