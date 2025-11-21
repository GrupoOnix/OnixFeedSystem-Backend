from typing import List
from pydantic import BaseModel, Field, ConfigDict


class SiloConfigModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    id: str
    name: str = Field(min_length=1, max_length=100)
    capacity: float = Field(gt=0)


class CageConfigModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    id: str
    name: str = Field(min_length=1, max_length=100)


class BlowerConfigModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    id: str
    name: str = Field(min_length=1, max_length=100)
    blower_type: str = "standard"
    non_feeding_power: float = Field(ge=0.0, le=100.0)
    blow_before_time: int = Field(ge=0, le=600)
    blow_after_time: int = Field(ge=0, le=600)


class DoserConfigModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    id: str
    name: str = Field(min_length=1, max_length=100)
    assigned_silo_id: str
    doser_type: str
    min_rate: float = Field(ge=0.0)
    max_rate: float = Field(gt=0.0)
    current_rate: float = Field(ge=0.0)


class SelectorConfigModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    id: str
    name: str = Field(min_length=1, max_length=100)
    selector_type: str = "standard"
    capacity: int = Field(gt=0)
    fast_speed: float = Field(ge=0.0, le=100.0)
    slow_speed: float = Field(ge=0.0, le=100.0)


class SensorConfigModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    id: str
    name: str = Field(min_length=1, max_length=100)
    sensor_type: str


class SlotAssignmentModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    slot_number: int = Field(gt=0)
    cage_id: str


class FeedingLineConfigModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    id: str
    line_name: str = Field(min_length=1, max_length=100)
    blower_config: BlowerConfigModel
    sensors_config: List[SensorConfigModel] = Field(default_factory=list)
    dosers_config: List[DoserConfigModel] = Field(min_length=1)
    selector_config: SelectorConfigModel
    slot_assignments: List[SlotAssignmentModel]


class SystemLayoutModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    silos: List[SiloConfigModel]
    cages: List[CageConfigModel]
    feeding_lines: List[FeedingLineConfigModel]



