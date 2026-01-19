"""DTOs para operaciones con sensores."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SensorDetailDTO:
    """DTO con información detallada de un sensor."""

    id: str
    name: str
    sensor_type: str
    is_enabled: bool
    warning_threshold: Optional[float]
    critical_threshold: Optional[float]


@dataclass
class SensorsListDTO:
    """DTO con lista de sensores de una línea."""

    line_id: str
    sensors: List[SensorDetailDTO]


@dataclass
class UpdateSensorDTO:
    """DTO para actualización de sensor."""

    name: Optional[str] = None
    is_enabled: Optional[bool] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    clear_warning_threshold: bool = False
    clear_critical_threshold: bool = False
