from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID


AllowedManualDosingUnit = Literal["KG_PER_MINUTE"]
AllowedFeedingPageMode = Literal["MANUAL", "CYCLIC"]
AllowedCyclicCageMode = Literal["NORMAL", "PAUSE", "FASTING"]


class LastValidManualFeedingConfigPayload(BaseModel):
    target_silo_id: str = Field(description="ID del silo objetivo")
    target_cage_id: str = Field(description="ID de la jaula objetivo")
    target_amount_kg: float = Field(gt=0, description="Cantidad objetivo en kg")
    dosing_rate_kg_per_min: float = Field(gt=0, description="Tasa de dosificación en kg/min")
    dosing_unit: AllowedManualDosingUnit = Field(description="Unidad de dosificación")
    blower_power_percentage: float = Field(
        ge=30,
        le=100,
        description="Potencia del blower en porcentaje",
    )


class LastValidManualFeedingConfigResponse(BaseModel):
    id: str
    line_id: str
    target_silo_id: str
    target_cage_id: str
    target_amount_kg: float
    dosing_rate_kg_per_min: float
    dosing_unit: AllowedManualDosingUnit
    blower_power_percentage: float
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_valid_against_current_layout: bool


class LastSelectedFeedingModePayload(BaseModel):
    selected_mode: AllowedFeedingPageMode = Field(description="Última opción seleccionada en la línea")


class LastSelectedFeedingModeResponse(BaseModel):
    id: str
    line_id: str
    selected_mode: AllowedFeedingPageMode
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LastValidCyclicCageConfigPayload(BaseModel):
    cage_id: str = Field(description="ID de la jaula")
    visits: Optional[int] = Field(
        default=None,
        ge=1,
        description="Cantidad de visitas para esta jaula",
    )
    quantity_kg: float = Field(ge=0, description="Cantidad total para esta jaula")
    rate_kg_per_min: float = Field(ge=0, description="Tasa de dosificación en kg/min")
    mode: AllowedCyclicCageMode = Field(description="Modo de la jaula")

    @field_validator("cage_id")
    @classmethod
    def validate_cage_id(cls, value: str) -> str:
        UUID(value)
        return value

    @model_validator(mode="after")
    def validate_quantity_and_rate_by_mode(self) -> "LastValidCyclicCageConfigPayload":
        if self.mode != "FASTING":
            if self.quantity_kg <= 0:
                raise ValueError(f"quantity_kg debe ser > 0 para el modo '{self.mode}'")
            if self.rate_kg_per_min <= 0:
                raise ValueError(f"rate_kg_per_min debe ser > 0 para el modo '{self.mode}'")
        return self


class LastValidCyclicFeedingConfigPayload(BaseModel):
    group_id: str = Field(description="ID del grupo de jaulas")
    doser_id: str = Field(description="ID del doser objetivo")
    visits: Optional[int] = Field(
        default=None,
        ge=1,
        description="Cantidad global de visitas por jaula (deprecated; fallback)",
    )
    blower_power_percentage: float = Field(
        ge=30,
        le=100,
        description="Potencia del blower en porcentaje",
    )
    wait_after_visit_seconds: float = Field(
        default=0,
        ge=0,
        description="Tiempo de espera en segundos después de cada visita cíclica, excepto la última.",
    )
    cage_configs: list[LastValidCyclicCageConfigPayload] = Field(
        min_length=1,
        description="Configuración por jaula",
    )

    @field_validator("group_id", "doser_id")
    @classmethod
    def validate_uuid(cls, value: str) -> str:
        UUID(value)
        return value

    @model_validator(mode="after")
    def validate_visits_fallback(self) -> "LastValidCyclicFeedingConfigPayload":
        for cage_config in self.cage_configs:
            if cage_config.mode != "FASTING" and cage_config.visits is None and self.visits is None:
                raise ValueError("Cada jaula activa debe declarar visits o la configuración debe incluir visits global")
        return self


class LastValidCyclicFeedingConfigResponse(BaseModel):
    id: str
    line_id: str
    group_id: str
    doser_id: str
    visits: Optional[int]
    blower_power_percentage: float
    wait_after_visit_seconds: float
    cage_configs: list[LastValidCyclicCageConfigPayload]
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_valid_against_current_layout: bool
