"""Modelos de API para el módulo de grupos de jaulas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from application.dtos.cage_group_dtos import (
    CageGroupMetricsResponse,
    CageGroupResponse,
    ListCageGroupsResponse,
)

# =============================================================================
# REQUEST MODELS
# =============================================================================


class CreateCageGroupRequestModel(BaseModel):
    """Request para crear un grupo de jaulas."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nombre único del grupo",
    )
    cage_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Lista de IDs de jaulas (UUIDs)",
    )
    description: Optional[str] = Field(
        None,
        description="Descripción opcional del grupo",
    )


class UpdateCageGroupRequestModel(BaseModel):
    """Request para actualizar un grupo de jaulas."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Nuevo nombre del grupo",
    )
    cage_ids: Optional[List[str]] = Field(
        None,
        min_length=1,
        description="Nueva lista de IDs de jaulas",
    )
    description: Optional[str] = Field(
        None,
        description="Nueva descripción (None para limpiar)",
    )


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class CageGroupMetricsModel(BaseModel):
    """Modelo para métricas calculadas de un grupo."""

    total_population: int = Field(
        ..., description="Población total de peces en el grupo"
    )
    total_biomass: float = Field(
        ..., description="Biomasa total en kg"
    )
    avg_weight: float = Field(
        ..., description="Peso promedio ponderado en gramos"
    )
    total_volume: float = Field(
        ..., description="Volumen total en m³"
    )
    avg_density: float = Field(
        ..., description="Densidad promedio en kg/m³"
    )

    @staticmethod
    def from_dto(dto: CageGroupMetricsResponse) -> "CageGroupMetricsModel":
        """Convierte DTO a modelo de API."""
        return CageGroupMetricsModel(
            total_population=dto.total_population,
            total_biomass=dto.total_biomass,
            avg_weight=dto.avg_weight,
            total_volume=dto.total_volume,
            avg_density=dto.avg_density,
        )


class CageGroupResponseModel(BaseModel):
    """Modelo de respuesta para un grupo de jaulas."""

    id: str = Field(..., description="ID único del grupo (UUID)")
    name: str = Field(..., description="Nombre del grupo")
    description: Optional[str] = Field(None, description="Descripción del grupo")
    cage_ids: List[str] = Field(..., description="Lista de IDs de jaulas incluidas")
    created_at: datetime = Field(..., description="Fecha de creación (UTC)")
    updated_at: datetime = Field(..., description="Fecha de última actualización (UTC)")
    metrics: CageGroupMetricsModel = Field(..., description="Métricas agregadas calculadas")

    @staticmethod
    def from_dto(dto: CageGroupResponse) -> "CageGroupResponseModel":
        """Convierte DTO a modelo de API."""
        return CageGroupResponseModel(
            id=dto.id,
            name=dto.name,
            description=dto.description,
            cage_ids=dto.cage_ids,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            metrics=CageGroupMetricsModel.from_dto(dto.metrics),
        )


class ListCageGroupsResponseModel(BaseModel):
    """Modelo de respuesta para listar grupos de jaulas."""

    groups: List[CageGroupResponseModel] = Field(
        ..., description="Lista de grupos de jaulas"
    )
    total: int = Field(..., description="Total de grupos (con filtros aplicados)")

    @staticmethod
    def from_dto(dto: ListCageGroupsResponse) -> "ListCageGroupsResponseModel":
        """Convierte DTO a modelo de API."""
        return ListCageGroupsResponseModel(
            groups=[CageGroupResponseModel.from_dto(g) for g in dto.groups],
            total=dto.total,
        )
