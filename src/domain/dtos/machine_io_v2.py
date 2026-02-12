from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from domain.enums import FeedingMode, SensorType


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


@dataclass(frozen=True)
class SensorReading:
    """
    Representa una lectura individual de un sensor en un momento específico.

    Este DTO se usa para transferir datos de sensores desde el PLC/simulador
    hacia las capas superiores de la aplicación.
    """

    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    timestamp: datetime
    is_warning: bool = False
    is_critical: bool = False

    def __post_init__(self):
        """Valida que la unidad sea correcta según el tipo de sensor."""
        expected_units = {
            SensorType.TEMPERATURE: "°C",
            SensorType.PRESSURE: "bar",
            SensorType.FLOW: "m³/min",
        }

        expected = expected_units.get(self.sensor_type)
        if expected and self.unit != expected:
            raise ValueError(
                f"Unidad incorrecta para sensor {self.sensor_type.value}: "
                f"esperado '{expected}', recibido '{self.unit}'"
            )


@dataclass(frozen=True)
class SensorReadings:
    """
    Colección de lecturas de sensores para una línea de alimentación.

    Agrupa todas las lecturas de sensores de una línea en un momento dado,
    facilitando la transmisión y visualización en el dashboard.
    """

    line_id: str
    readings: List[SensorReading]
    timestamp: datetime


# =============================================================================
# DTOs para comandos de control individual de dispositivos
# =============================================================================


@dataclass(frozen=True)
class BlowerCommand:
    """Comando para controlar un blower específico."""

    blower_id: str
    blower_name: str
    line_id: str
    line_name: str
    power_percentage: float


@dataclass(frozen=True)
class DoserCommand:
    """Comando para controlar un doser específico."""

    doser_id: str
    doser_name: str
    line_id: str
    line_name: str
    rate_percentage: float


@dataclass(frozen=True)
class SelectorCommand:
    """Comando para controlar un selector específico."""

    selector_id: str
    selector_name: str
    line_id: str
    line_name: str
    slot_number: Optional[int] = None  # None significa reset/home


@dataclass(frozen=True)
class CoolerCommand:
    """Comando para controlar un cooler específico."""

    cooler_id: str
    cooler_name: str
    line_id: str
    line_name: str
    power_percentage: float
