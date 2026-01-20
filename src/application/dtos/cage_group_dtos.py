"""DTOs para el módulo de grupos de jaulas."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

# =============================================================================
# REQUEST DTOs
# =============================================================================


@dataclass
class CreateCageGroupRequest:
    """Request para crear un grupo de jaulas."""

    name: str
    cage_ids: List[str]  # UUIDs como strings
    description: Optional[str] = None


@dataclass
class UpdateCageGroupRequest:
    """Request para actualizar un grupo de jaulas."""

    name: Optional[str] = None
    cage_ids: Optional[List[str]] = None  # UUIDs como strings
    description: Optional[str] = None


# =============================================================================
# RESPONSE DTOs
# =============================================================================


@dataclass
class CageGroupMetricsResponse:
    """Response para métricas calculadas de un grupo de jaulas."""

    total_population: int
    total_biomass: float
    avg_weight: float
    total_volume: float
    avg_density: float


@dataclass
class CageGroupResponse:
    """Response para un grupo de jaulas."""

    id: str
    name: str
    description: Optional[str]
    cage_ids: List[str]
    created_at: datetime
    updated_at: datetime
    metrics: CageGroupMetricsResponse


@dataclass
class ListCageGroupsResponse:
    """Response para listar grupos de jaulas."""

    groups: List[CageGroupResponse]
    total: int
