from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SiloBatchFoodDTO:
    id: str
    name: str
    code: str
    provider: str


@dataclass
class SiloInventoryBatchDTO:
    id: str
    food: Optional[SiloBatchFoodDTO]
    remaining_quantity_kg: float
    reserved_quantity_kg: float
    available_quantity_kg: float
    position: int
    status: str
    received_at: datetime
    created_by_operator_id: str
    created_at: datetime
    updated_at: datetime


@dataclass
class SiloDTO:
    """DTO para representar un silo en respuestas de API."""

    id: str
    name: str
    capacity_kg: float
    total_stock_kg: float
    reserved_stock_kg: float
    available_stock_kg: float
    fill_percentage: float
    is_assigned: bool
    created_at: datetime
    line_id: Optional[str] = None
    line_name: Optional[str] = None
    line_ids: Optional[List[str]] = None
    line_names: Optional[List[str]] = None
    active_batches: Optional[List[SiloInventoryBatchDTO]] = None


@dataclass
class CreateSiloRequest:
    """Request para crear un nuevo silo."""

    name: str
    capacity_kg: float


@dataclass
class UpdateSiloRequest:
    """Request para actualizar un silo existente."""

    name: Optional[str] = None
    capacity_kg: Optional[float] = None


@dataclass
class ListSilosRequest:
    """Request para listar silos con filtros opcionales."""

    is_assigned: Optional[bool] = None


@dataclass
class ListSilosResponse:
    """Response con lista de silos."""

    silos: List[SiloDTO]
