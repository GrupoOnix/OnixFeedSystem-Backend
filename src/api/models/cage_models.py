"""Modelos de API para el módulo de jaulas."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from application.dtos.cage_dtos import (
    CageListItemResponse,
    CageResponse,
    ListCagesResponse,
    PaginationInfo,
    PopulationEventResponse,
    PopulationHistoryResponse,
)

# =============================================================================
# REQUEST MODELS
# =============================================================================


class CreateCageRequestModel(BaseModel):
    """Request para crear una jaula."""

    name: str = Field(..., min_length=1, max_length=100, description="Nombre de la jaula")
    fcr: Optional[float] = Field(None, ge=0.5, le=3.0, description="Feed Conversion Ratio")
    volume_m3: Optional[float] = Field(None, gt=0, description="Volumen en metros cúbicos")
    max_density_kg_m3: Optional[float] = Field(None, gt=0, description="Densidad máxima en kg/m³")
    transport_time_seconds: Optional[int] = Field(None, ge=0, description="Tiempo de transporte en segundos")
    blower_power: Optional[int] = Field(None, ge=30, le=100, description="Potencia del blower (30-100)")


class UpdateCageRequestModel(BaseModel):
    """Request para actualizar una jaula."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Nuevo nombre")
    status: Optional[str] = Field(None, description="Nuevo estado: AVAILABLE, IN_USE, MAINTENANCE")


class UpdateCageConfigRequestModel(BaseModel):
    """Request para actualizar la configuración."""

    fcr: Optional[float] = Field(None, ge=0.5, le=3.0, description="Feed Conversion Ratio")
    volume_m3: Optional[float] = Field(None, gt=0, description="Volumen en metros cúbicos")
    max_density_kg_m3: Optional[float] = Field(None, gt=0, description="Densidad máxima en kg/m³")
    transport_time_seconds: Optional[int] = Field(None, ge=0, description="Tiempo de transporte en segundos")
    blower_power: Optional[int] = Field(None, ge=30, le=100, description="Potencia del blower (30-100)")
    daily_feeding_target_kg: Optional[float] = Field(None, ge=0, description="Meta de alimentación diaria en kg")


class SetPopulationRequestModel(BaseModel):
    """Request para establecer la población inicial."""

    fish_count: int = Field(..., gt=0, description="Cantidad de peces")
    avg_weight_grams: float = Field(..., gt=0, description="Peso promedio en gramos")
    event_date: date = Field(..., description="Fecha del evento")
    note: Optional[str] = Field(None, max_length=500, description="Nota opcional")


class RegisterMortalityRequestModel(BaseModel):
    """Request para registrar mortalidad."""

    dead_count: int = Field(..., gt=0, description="Cantidad de peces muertos")
    event_date: date = Field(..., description="Fecha del evento")
    note: Optional[str] = Field(None, max_length=500, description="Nota opcional")


class UpdateBiometryRequestModel(BaseModel):
    """Request para actualizar biometría."""

    avg_weight_grams: float = Field(..., gt=0, description="Peso promedio en gramos")
    event_date: date = Field(..., description="Fecha del muestreo")
    note: Optional[str] = Field(None, max_length=500, description="Nota opcional")


class HarvestRequestModel(BaseModel):
    """Request para registrar cosecha."""

    count: int = Field(..., gt=0, description="Cantidad de peces cosechados")
    event_date: date = Field(..., description="Fecha de la cosecha")
    note: Optional[str] = Field(None, max_length=500, description="Nota opcional")


class AdjustPopulationRequestModel(BaseModel):
    """Request para ajustar la población."""

    new_fish_count: int = Field(..., ge=0, description="Nueva cantidad total de peces")
    event_date: date = Field(..., description="Fecha del ajuste")
    note: Optional[str] = Field(None, max_length=500, description="Nota explicativa")


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class CageConfigResponseModel(BaseModel):
    """Response para la configuración de una jaula."""

    fcr: Optional[float] = None
    volume_m3: Optional[float] = None
    max_density_kg_m3: Optional[float] = None
    transport_time_seconds: Optional[int] = None
    blower_power: Optional[int] = None
    daily_feeding_target_kg: Optional[float] = None


class CageResponseModel(BaseModel):
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
    config: CageConfigResponseModel

    # Calculados
    current_density_kg_m3: Optional[float]

    # Alimentación del día (calculado)
    today_feeding_kg: float = 0.0

    @classmethod
    def from_dto(cls, dto: CageResponse) -> "CageResponseModel":
        """Convierte DTO a modelo de API."""
        return cls(
            id=dto.id,
            name=dto.name,
            status=dto.status,
            created_at=dto.created_at,
            fish_count=dto.fish_count,
            avg_weight_grams=dto.avg_weight_grams,
            biomass_kg=dto.biomass_kg,
            config=CageConfigResponseModel(
                fcr=dto.config.fcr,
                volume_m3=dto.config.volume_m3,
                max_density_kg_m3=dto.config.max_density_kg_m3,
                transport_time_seconds=dto.config.transport_time_seconds,
                blower_power=dto.config.blower_power,
                daily_feeding_target_kg=dto.config.daily_feeding_target_kg,
            ),
            current_density_kg_m3=dto.current_density_kg_m3,
            today_feeding_kg=dto.today_feeding_kg,
        )


class CageListItemResponseModel(BaseModel):
    """Response para un item de lista de jaulas."""

    id: str
    name: str
    status: str
    fish_count: int
    avg_weight_grams: Optional[float]
    biomass_kg: float
    created_at: datetime

    # Configuración
    config: CageConfigResponseModel

    # Calculados
    current_density_kg_m3: Optional[float]

    # Alimentación del día (calculado)
    today_feeding_kg: float = 0.0

    @classmethod
    def from_dto(cls, dto: CageListItemResponse) -> "CageListItemResponseModel":
        """Convierte DTO a modelo de API."""
        return cls(
            id=dto.id,
            name=dto.name,
            status=dto.status,
            fish_count=dto.fish_count,
            avg_weight_grams=dto.avg_weight_grams,
            biomass_kg=dto.biomass_kg,
            created_at=dto.created_at,
            config=CageConfigResponseModel(
                fcr=dto.config.fcr,
                volume_m3=dto.config.volume_m3,
                max_density_kg_m3=dto.config.max_density_kg_m3,
                transport_time_seconds=dto.config.transport_time_seconds,
                blower_power=dto.config.blower_power,
                daily_feeding_target_kg=dto.config.daily_feeding_target_kg,
            ),
            current_density_kg_m3=dto.current_density_kg_m3,
            today_feeding_kg=dto.today_feeding_kg,
        )


class ListCagesResponseModel(BaseModel):
    """Response para listar jaulas."""

    cages: List[CageListItemResponseModel]
    total: int

    @classmethod
    def from_dto(cls, dto: ListCagesResponse) -> "ListCagesResponseModel":
        """Convierte DTO a modelo de API."""
        return cls(
            cages=[CageListItemResponseModel.from_dto(c) for c in dto.cages],
            total=dto.total,
        )


class PopulationEventResponseModel(BaseModel):
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

    @classmethod
    def from_dto(cls, dto: PopulationEventResponse) -> "PopulationEventResponseModel":
        """Convierte DTO a modelo de API."""
        return cls(
            id=dto.id,
            cage_id=dto.cage_id,
            event_type=dto.event_type,
            event_date=dto.event_date,
            fish_count_delta=dto.fish_count_delta,
            new_fish_count=dto.new_fish_count,
            avg_weight_grams=dto.avg_weight_grams,
            biomass_kg=dto.biomass_kg,
            note=dto.note,
            created_at=dto.created_at,
        )


class PaginationInfoModel(BaseModel):
    """Información de paginación."""

    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

    @classmethod
    def from_dto(cls, dto: PaginationInfo) -> "PaginationInfoModel":
        """Convierte DTO a modelo de API."""
        return cls(
            total=dto.total,
            limit=dto.limit,
            offset=dto.offset,
            has_next=dto.has_next,
            has_previous=dto.has_previous,
        )


class PopulationHistoryResponseModel(BaseModel):
    """Response para historial de población."""

    events: List[PopulationEventResponseModel]
    pagination: PaginationInfoModel

    @classmethod
    def from_dto(cls, dto: PopulationHistoryResponse) -> "PopulationHistoryResponseModel":
        """Convierte DTO a modelo de API."""
        return cls(
            events=[PopulationEventResponseModel.from_dto(e) for e in dto.events],
            pagination=PaginationInfoModel.from_dto(dto.pagination),
        )
