from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


AllowedManualDosingUnit = Literal["KG_PER_MINUTE"]


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
