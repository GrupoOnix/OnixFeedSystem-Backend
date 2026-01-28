"""DTOs para el módulo de jaulas."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

# =============================================================================
# REQUEST DTOs
# =============================================================================


@dataclass
class CreateCageRequest:
    """Request para crear una jaula."""

    name: str
    fcr: Optional[float] = None
    volume_m3: Optional[float] = None
    max_density_kg_m3: Optional[float] = None
    transport_time_seconds: Optional[int] = None
    blower_power: Optional[int] = None


@dataclass
class UpdateCageRequest:
    """Request para actualizar una jaula (nombre y/o status)."""

    name: Optional[str] = None
    status: Optional[str] = None  # AVAILABLE, IN_USE, MAINTENANCE


@dataclass
class UpdateCageConfigRequest:
    """Request para actualizar la configuración de una jaula."""

    fcr: Optional[float] = None
    volume_m3: Optional[float] = None
    max_density_kg_m3: Optional[float] = None
    transport_time_seconds: Optional[int] = None
    blower_power: Optional[int] = None


@dataclass
class SetPopulationRequest:
    """Request para establecer la población inicial."""

    fish_count: int
    avg_weight_grams: float
    event_date: date
    note: Optional[str] = None


@dataclass
class AddFishRequest:
    """Request para agregar peces (resiembra)."""

    count: int
    avg_weight_grams: Optional[float] = None
    event_date: date = None
    note: Optional[str] = None


@dataclass
class RegisterMortalityRequest:
    """Request para registrar mortalidad."""

    dead_count: int
    event_date: date
    note: Optional[str] = None


@dataclass
class UpdateBiometryRequest:
    """Request para actualizar biometría."""

    avg_weight_grams: float
    event_date: date
    note: Optional[str] = None


@dataclass
class HarvestRequest:
    """Request para registrar cosecha."""

    count: int
    event_date: date
    note: Optional[str] = None


@dataclass
class AdjustPopulationRequest:
    """Request para ajustar manualmente la población."""

    new_fish_count: int
    event_date: date
    note: Optional[str] = None


# =============================================================================
# RESPONSE DTOs
# =============================================================================


@dataclass
class CageConfigResponse:
    """Response para la configuración de una jaula."""

    fcr: Optional[float]
    volume_m3: Optional[float]
    max_density_kg_m3: Optional[float]
    transport_time_seconds: Optional[int]
    blower_power: Optional[int]


@dataclass
class CageResponse:
    """Response para una jaula."""

    id: str
    name: str
    status: str
    created_at: datetime

    # Población
    fish_count: int
    avg_weight_grams: Optional[float]
    biomass_kg: float

    # Configuración
    config: CageConfigResponse

    # Calculados
    current_density_kg_m3: Optional[float]


@dataclass
class CageListItemResponse:
    """Response para un item de lista de jaulas."""

    id: str
    name: str
    status: str
    fish_count: int
    avg_weight_grams: Optional[float]
    biomass_kg: float
    created_at: datetime


@dataclass
class ListCagesResponse:
    """Response para listar jaulas."""

    cages: List[CageListItemResponse]
    total: int


# =============================================================================
# POPULATION EVENT DTOs
# =============================================================================


@dataclass
class PopulationEventResponse:
    """Response para un evento de población."""

    id: str
    cage_id: str
    event_type: str
    event_date: date
    fish_count_delta: int
    new_fish_count: int
    avg_weight_grams: Optional[float]
    biomass_kg: Optional[float]
    note: Optional[str]
    created_at: datetime


@dataclass
class PaginationInfo:
    """Información de paginación."""

    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


@dataclass
class PopulationHistoryResponse:
    """Response para historial de población."""

    events: List[PopulationEventResponse]
    pagination: PaginationInfo
