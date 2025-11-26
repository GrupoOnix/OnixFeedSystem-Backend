from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class RegisterBiometryRequest:
    """Request para registrar biometría de una jaula."""
    sampling_date: date
    fish_count: Optional[int] = None
    average_weight_g: Optional[float] = None
    note: Optional[str] = None


@dataclass
class BiometryLogItemResponse:
    """Response item para listado de registros de biometría."""
    biometry_id: str
    cage_id: str
    old_fish_count: Optional[int]
    new_fish_count: Optional[int]
    old_average_weight_g: Optional[float]
    new_average_weight_g: Optional[float]
    sampling_date: date
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
class PaginatedBiometryResponse:
    """Response paginado para listado de registros de biometría."""
    logs: list[BiometryLogItemResponse]
    pagination: PaginationInfo
