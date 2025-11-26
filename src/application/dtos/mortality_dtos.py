from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class RegisterMortalityRequest:
    """Request para registrar mortalidad de una jaula."""
    dead_fish_count: int
    mortality_date: date
    note: Optional[str] = None


@dataclass
class MortalityLogItemResponse:
    """Response item para listado de registros de mortalidad."""
    mortality_id: str
    cage_id: str
    dead_fish_count: int
    mortality_date: date
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
class PaginatedMortalityResponse:
    """Response paginado para listado de registros de mortalidad."""
    logs: list[MortalityLogItemResponse]
    pagination: PaginationInfo
