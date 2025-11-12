from dataclasses import dataclass
from typing import List, Dict, Any

# ============================================================================
# DTOs de Agregados Independientes
# ============================================================================

@dataclass(frozen=True)
class SiloConfigDTO:
    id: str
    name: str
    capacity: float


@dataclass(frozen=True)
class CageConfigDTO:
    id: str
    name: str


# ============================================================================
# DTOs de Componentes (Hijos de FeedingLine)
# ============================================================================

@dataclass(frozen=True)
class BlowerConfigDTO:
    id: str
    name: str
    non_feeding_power: float
    blow_before_time: int
    blow_after_time: int


@dataclass(frozen=True)
class SensorConfigDTO:
    id: str
    name: str
    sensor_type: str  # Se recibe como string desde API, se convierte a enum en el caso de uso


@dataclass(frozen=True)
class DoserConfigDTO:
    id: str
    name: str
    assigned_silo_id: str
    doser_type: str
    min_rate: float
    max_rate: float
    current_rate: float


@dataclass(frozen=True)
class SelectorConfigDTO:
    id: str
    name: str
    capacity: int
    fast_speed: float
    slow_speed: float


# ============================================================================
# DTO de Asignación (Value Object)
# ============================================================================

@dataclass(frozen=True)
class SlotAssignmentDTO:
    slot_number: int
    cage_id: str


# ============================================================================
# DTO de Agregado Dependiente (Contenedor de Hijos)
# ============================================================================

@dataclass(frozen=True)
class FeedingLineConfigDTO:
    id: str
    line_name: str
    blower_config: BlowerConfigDTO
    sensors_config: List[SensorConfigDTO]
    dosers_config: List[DoserConfigDTO]
    selector_config: SelectorConfigDTO
    slot_assignments: List[SlotAssignmentDTO]


# ============================================================================
# DTO Raíz (El Canvas Completo) - Request y Response
# ============================================================================

@dataclass(frozen=True)
class SystemLayoutDTO:
    """
    DTO del layout completo del sistema.
    
    Usado tanto para request (entrada) como response (salida).
    En response, los IDs son UUIDs reales en lugar de temporales.
    """
    silos: List[SiloConfigDTO]
    cages: List[CageConfigDTO]
    feeding_lines: List[FeedingLineConfigDTO]
    presentation_data: Dict[str, Any]
