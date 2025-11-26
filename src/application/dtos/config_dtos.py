from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UpdateCageConfigRequest:
    """Request para actualizar configuración de una jaula."""
    fcr: Optional[float] = None
    volume_m3: Optional[float] = None
    max_density_kg_m3: Optional[float] = None
    feeding_table_id: Optional[str] = None
    transport_time_seconds: Optional[int] = None
    change_reason: Optional[str] = None


@dataclass
class ConfigChangeLogItemResponse:
    """Response item para listado de cambios de configuración."""
    change_id: str
    cage_id: str
    field_name: str
    old_value: str
    new_value: str
    change_reason: Optional[str]
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
class PaginatedConfigChangesResponse:
    """Response paginado para listado de cambios de configuración."""
    logs: list[ConfigChangeLogItemResponse]
    pagination: PaginationInfo
