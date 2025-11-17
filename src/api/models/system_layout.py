from typing import List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# Configuración estricta global para todos los modelos
STRICT_CONFIG = ConfigDict(extra='forbid')


class SiloConfigModel(BaseModel):
    """Configuración de un Silo."""
    
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            "example": {
                "id": "temp_silo_1",
                "name": "Silo A",
                "capacity": 1000.0
            }
        }
    )
    
    id: str = Field(
        ...,
        description="ID del silo (UUID real o ID temporal para creación)",
        examples=["550e8400-e29b-41d4-a716-446655440000", "temp_silo_1"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del silo",
        examples=["Silo A", "Silo Principal"]
    )
    capacity: float = Field(
        ...,
        gt=0,
        description="Capacidad del silo en kilogramos",
        examples=[1000.0, 5000.0]
    )


class CageConfigModel(BaseModel):
    """Configuración de una Jaula."""
    
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            "example": {
                "id": "temp_cage_1",
                "name": "Jaula 1"
            }
        }
    )
    
    id: str = Field(
        ...,
        description="ID de la jaula (UUID real o ID temporal para creación)",
        examples=["550e8400-e29b-41d4-a716-446655440000", "temp_cage_1"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre de la jaula",
        examples=["Jaula 1", "Jaula Norte"]
    )


class BlowerConfigModel(BaseModel):
    """Configuración de un Soplador."""
    
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            "example": {
                "id": "temp_blower_1",
                "name": "Soplador Principal",
                "blower_type": "standard",
                "non_feeding_power": 50.0,
                "blow_before_time": 5,
                "blow_after_time": 3
            }
        }
    )
    
    id: str = Field(
        ...,
        description="ID del soplador (temporal o UUID)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del soplador"
    )
    blower_type: str = Field(
        default="standard",
        description="Tipo de soplador",
        examples=["standard", "turbo"]
    )
    non_feeding_power: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Potencia en modo no-alimentación (porcentaje 0-100)"
    )
    blow_before_time: int = Field(
        ...,
        ge=0,
        le=600,
        description="Tiempo de soplado antes de alimentar (segundos)"
    )
    blow_after_time: int = Field(
        ...,
        ge=0,
        le=600,
        description="Tiempo de soplado después de alimentar (segundos)"
    )


class DoserConfigModel(BaseModel):
    """Configuración de un Dosificador."""
    
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            "example": {
                "id": "temp_doser_1",
                "name": "Dosificador 1",
                "assigned_silo_id": "temp_silo_1",
                "doser_type": "volumetric",
                "min_rate": 10.0,
                "max_rate": 100.0,
                "current_rate": 50.0
            }
        }
    )
    
    id: str = Field(
        ...,
        description="ID del dosificador (temporal o UUID)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del dosificador"
    )
    assigned_silo_id: str = Field(
        ...,
        description="ID del silo asignado (UUID real o ID temporal)",
        examples=["550e8400-e29b-41d4-a716-446655440000", "temp_silo_1"]
    )
    doser_type: str = Field(
        ...,
        description="Tipo de dosificador",
        examples=["volumetric", "gravimetric"]
    )
    min_rate: float = Field(
        ...,
        ge=0.0,
        description="Tasa mínima de dosificación (kg/min)"
    )
    max_rate: float = Field(
        ...,
        gt=0.0,
        description="Tasa máxima de dosificación (kg/min)"
    )
    current_rate: float = Field(
        ...,
        ge=0.0,
        description="Tasa actual de dosificación (kg/min)"
    )


class SelectorConfigModel(BaseModel):
    """Configuración de un Selector."""
    
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            "example": {
                "id": "temp_selector_1",
                "name": "Selector Principal",
                "selector_type": "standard",
                "capacity": 4,
                "fast_speed": 80.0,
                "slow_speed": 20.0
            }
        }
    )
    
    id: str = Field(
        ...,
        description="ID del selector (temporal, se regenera en cada sincronización)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del selector"
    )
    selector_type: str = Field(
        default="standard",
        description="Tipo de selector",
        examples=["standard"]
    )
    capacity: int = Field(
        ...,
        gt=0,
        description="Capacidad del selector (número de slots/ranuras)"
    )
    fast_speed: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Velocidad rápida (porcentaje 0-100)"
    )
    slow_speed: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Velocidad lenta (porcentaje 0-100)"
    )


class SensorConfigModel(BaseModel):
    """Configuración de un Sensor."""
    
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            "example": {
                "id": "temp_sensor_1",
                "name": "Sensor de Temperatura 1",
                "sensor_type": "TEMPERATURE"
            }
        }
    )
    
    id: str = Field(
        ...,
        description="ID del sensor (temporal o UUID)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del sensor"
    )
    sensor_type: str = Field(
        ...,
        description="Tipo de sensor (TEMPERATURE, PRESSURE, FLOW)",
        examples=["TEMPERATURE", "PRESSURE", "FLOW"]
    )


class SlotAssignmentModel(BaseModel):
    """Asignación de una jaula a un slot del selector."""
    
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            "example": {
                "slot_number": 1,
                "cage_id": "temp_cage_1"
            }
        }
    )
    
    slot_number: int = Field(
        ...,
        gt=0,
        description="Número del slot (debe ser >= 1)"
    )
    cage_id: str = Field(
        ...,
        description="ID de la jaula asignada (UUID real o ID temporal)",
        examples=["550e8400-e29b-41d4-a716-446655440000", "temp_cage_1"]
    )


class FeedingLineConfigModel(BaseModel):
    """Configuración completa de una Línea de Alimentación."""
    
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            "example": {
                "id": "temp_line_1",
                "line_name": "Linea Principal",
                "blower_config": {
                    "id": "temp_blower_1",
                    "name": "Soplador 1",
                    "blower_type": "standard",
                    "non_feeding_power": 50.0,
                    "blow_before_time": 5,
                    "blow_after_time": 3
                },
                "sensors_config": [
                    {
                        "id": "temp_sensor_1",
                        "name": "Sensor de Temperatura 1",
                        "sensor_type": "TEMPERATURE"
                    }
                ],
                "dosers_config": [
                    {
                        "id": "temp_doser_1",
                        "name": "Dosificador 1",
                        "assigned_silo_id": "temp_silo_1",
                        "doser_type": "volumetric",
                        "min_rate": 10.0,
                        "max_rate": 100.0,
                        "current_rate": 50.0
                    }
                ],
                "selector_config": {
                    "id": "temp_selector_1",
                    "name": "Selector 1",
                    "selector_type": "standard",
                    "capacity": 4,
                    "fast_speed": 80.0,
                    "slow_speed": 20.0
                },
                "slot_assignments": [
                    {"slot_number": 1, "cage_id": "temp_cage_1"}
                ]
            }
        }
    )
    
    id: str = Field(
        ...,
        description="ID de la línea (UUID real o ID temporal para creación)",
        examples=["550e8400-e29b-41d4-a716-446655440000", "temp_line_1"]
    )
    line_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre de la línea de alimentación"
    )
    blower_config: BlowerConfigModel = Field(
        ...,
        description="Configuración del soplador"
    )
    sensors_config: List[SensorConfigModel] = Field(
        default_factory=list,
        description="Lista de sensores (opcional, puede estar vacío [])"
    )
    dosers_config: List[DoserConfigModel] = Field(
        ...,
        min_length=1,
        description="Lista de dosificadores (mínimo 1 requerido)"
    )
    selector_config: SelectorConfigModel = Field(
        ...,
        description="Configuración del selector"
    )
    slot_assignments: List[SlotAssignmentModel] = Field(
        ...,
        description="Asignaciones de jaulas a slots (obligatorio, puede estar vacío [])"
    )


class SystemLayoutModel(BaseModel):
    """
    Modelo del layout completo del sistema.
    
    Usado tanto para request (con IDs temporales) como response (con UUIDs reales).
    Este es el modelo raíz que contiene todos los agregados del sistema.
    """
    
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            "example": {
                "silos": [
                    {"id": "temp_silo_1", "name": "Silo A", "capacity": 1000.0}
                ],
                "cages": [
                    {"id": "temp_cage_1", "name": "Jaula 1"}
                ],
                "feeding_lines": [
                    {
                        "id": "temp_line_1",
                        "line_name": "Linea Principal",
                        "blower_config": {
                            "id": "temp_blower_1",
                            "name": "Soplador 1",
                            "non_feeding_power": 50.0,
                            "blow_before_time": 5,
                            "blow_after_time": 3
                        },
                        "sensors_config": [],
                        "dosers_config": [
                            {
                                "id": "temp_doser_1",
                                "name": "Dosificador 1",
                                "assigned_silo_id": "temp_silo_1",
                                "doser_type": "volumetric",
                                "min_rate": 10.0,
                                "max_rate": 100.0,
                                "current_rate": 50.0
                            }
                        ],
                        "selector_config": {
                            "id": "temp_selector_1",
                            "name": "Selector 1",
                            "capacity": 4,
                            "fast_speed": 80.0,
                            "slow_speed": 20.0
                        },
                        "slot_assignments": [
                            {"slot_number": 1, "cage_id": "temp_cage_1"}
                        ]
                    }
                ]
            }
        }
    )
    
    silos: List[SiloConfigModel] = Field(
        ...,
        description="Lista de silos del sistema (obligatorio, puede estar vacío [])"
    )
    cages: List[CageConfigModel] = Field(
        ...,
        description="Lista de jaulas del sistema (obligatorio, puede estar vacío [])"
    )
    feeding_lines: List[FeedingLineConfigModel] = Field(
        ...,
        description="Lista de líneas de alimentación (obligatorio, puede estar vacío [])"
    )



