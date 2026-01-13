from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class FoodDTO:
    """DTO para representar un alimento en respuestas de API."""

    id: str
    name: str
    provider: str
    code: str
    ppk: float
    size_mm: float
    energy: float
    kg_per_liter: float
    active: bool
    created_at: datetime
    updated_at: datetime
    display_name: str  # Formato: "{name} ({code})"


@dataclass
class CreateFoodRequest:
    """Request para crear un nuevo alimento."""

    name: str
    provider: str
    code: str
    ppk: float
    size_mm: float
    energy: float
    kg_per_liter: float
    active: bool = True


@dataclass
class UpdateFoodRequest:
    """Request para actualizar un alimento existente."""

    name: Optional[str] = None
    provider: Optional[str] = None
    code: Optional[str] = None
    ppk: Optional[float] = None
    size_mm: Optional[float] = None
    energy: Optional[float] = None
    kg_per_liter: Optional[float] = None


@dataclass
class ToggleFoodActiveRequest:
    """Request para activar/desactivar un alimento."""

    active: bool


@dataclass
class ListFoodsResponse:
    """Response con lista de alimentos."""

    foods: List[FoodDTO]


@dataclass
class FoodDetailResponse:
    """Response con detalle de un alimento."""

    food: FoodDTO
