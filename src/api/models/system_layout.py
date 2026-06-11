from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SiloConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=100)
    capacity: float = Field(gt=0)
    food_id: Optional[str] = Field(default=None)
    stock_level: Optional[float] = Field(default=None, ge=0)


class CageConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=100)


class BlowerConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=100)
    blower_type: str = "standard"
    non_feeding_power: float = Field(ge=0.0, le=100.0)
    blow_before_time: int = Field(ge=0, le=600)
    blow_after_time: int = Field(ge=0, le=600)


class DoserConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=100)
    assigned_silo_ids: List[str] = Field(min_length=1)
    doser_type: str
    min_rate: float = Field(ge=0.0)
    max_rate: float = Field(gt=0.0, description="Tasa máxima del dosificador en kg/min")
    max_rate_unit: Literal["kg/min"] = Field(default="kg/min", description="Unidad de max_rate")
    current_rate: float = Field(ge=0.0)
    speed_percentage: int = Field(default=50, ge=1, le=100)
    calibrated_grams_per_second: Optional[float] = Field(default=None, gt=0.0)
    pulse_on_time: Optional[float] = Field(default=None, gt=0.0)
    pulse_off_time: Optional[float] = Field(default=None, ge=0.0)
    pulse_speed: Optional[int] = Field(default=None, ge=1, le=100)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_silo_field(cls, data: Any) -> Any:
        if isinstance(data, dict) and "assigned_silo_id" in data:
            data = data.copy()
            legacy_silo_id = data.pop("assigned_silo_id")
            data.setdefault("assigned_silo_ids", [legacy_silo_id])
        return data

    @field_validator("assigned_silo_ids")
    @classmethod
    def validate_unique_silo_ids(cls, value: List[str]) -> List[str]:
        if len(set(value)) != len(value):
            raise ValueError("assigned_silo_ids no puede contener IDs duplicados")
        return value

    @property
    def assigned_silo_id(self) -> str:
        return self.assigned_silo_ids[0]


class SelectorConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=100)
    selector_type: str = "standard"
    capacity: int = Field(gt=0)
    fast_speed: float = Field(ge=0.0, le=100.0)
    slow_speed: float = Field(ge=0.0, le=100.0)


class SensorConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=100)
    sensor_type: str


class CoolerConfigModel(BaseModel):
    """Configuración del Cooler (enfriador de aire) - componente opcional."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=100)
    cooling_power_percentage: float = Field(ge=0.0, le=100.0)
    is_on: bool = False


class SlotAssignmentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot_number: int = Field(gt=0)
    cage_id: str


class FeedingLineConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    line_name: str = Field(min_length=1, max_length=100)
    status: str = "AVAILABLE"
    locked_by: Optional[str] = None
    locked_reason: Optional[str] = None
    locked_at: Optional[datetime] = None
    blower_config: BlowerConfigModel
    cooler_config: Optional[CoolerConfigModel] = None  # Componente opcional
    sensors_config: List[SensorConfigModel] = Field(default_factory=list)
    dosers_config: List[DoserConfigModel] = Field(min_length=1)
    selector_config: SelectorConfigModel
    slot_assignments: List[SlotAssignmentModel]


class SystemLayoutModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    silos: List[SiloConfigModel]
    cages: List[CageConfigModel]
    feeding_lines: List[FeedingLineConfigModel]
