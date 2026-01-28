from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SiloDTO:
    """DTO para representar un silo en respuestas de API."""

    id: str
    name: str
    capacity_kg: float
    stock_level_kg: float
    is_assigned: bool
    created_at: datetime
    line_id: Optional[str] = None
    line_name: Optional[str] = None
    food_id: Optional[str] = None


@dataclass
class CreateSiloRequest:
    """Request para crear un nuevo silo."""

    name: str
    capacity_kg: float
    stock_level_kg: float = 0.0


@dataclass
class UpdateSiloRequest:
    """Request para actualizar un silo existente."""

    name: Optional[str] = None
    capacity_kg: Optional[float] = None
    stock_level_kg: Optional[float] = None
    food_id: Optional[str] = None


@dataclass
class ListSilosRequest:
    """Request para listar silos con filtros opcionales."""

    is_assigned: Optional[bool] = None


@dataclass
class ListSilosResponse:
    """Response con lista de silos."""

    silos: List[SiloDTO]
