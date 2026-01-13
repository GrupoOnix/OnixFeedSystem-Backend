"""
Value Objects del dominio de Feeding System.

Este módulo centraliza todos los Value Objects organizados por categoría.
Los imports se mantienen simples desde fuera del módulo:

    from domain.value_objects import CageId, FishCount, Weight
"""

# Identifiers
# Aquaculture
from .aquaculture import (
    FCR,
    FishCount,
)

# Log Entries
from .biometry_log_entry import BiometryLogEntry
from .config_change_log_entry import ConfigChangeLogEntry

# Feeding Specs
from .feeding_specs import (
    BlowDurationInSeconds,
    BlowerPowerPercentage,
    DosingRange,
    DosingRate,
    SelectorCapacity,
    SelectorSpeedProfile,
)
from .identifiers import (
    BlowerId,
    CageId,
    DoserId,
    FeedingTableId,
    FoodId,
    LineId,
    OperationId,
    SelectorId,
    SensorId,
    SessionId,
    SiloId,
)

# Measurements
from .measurements import (
    Density,
    Volume,
    Weight,
)
from .mortality_log_entry import MortalityLogEntry

# Names
from .names import (
    BlowerName,
    CageName,
    DoserName,
    FoodName,
    LineName,
    SelectorName,
    SensorName,
    SiloName,
)

__all__ = [
    # Identifiers
    "LineId",
    "CageId",
    "SiloId",
    "BlowerId",
    "DoserId",
    "SelectorId",
    "SensorId",
    "FeedingTableId",
    "SessionId",
    "OperationId",
    "FoodId",
    # Names
    "LineName",
    "CageName",
    "SiloName",
    "BlowerName",
    "DoserName",
    "SelectorName",
    "SensorName",
    "FoodName",
    # Measurements
    "Weight",
    "Volume",
    "Density",
    # Feeding Specs
    "BlowerPowerPercentage",
    "BlowDurationInSeconds",
    "DosingRate",
    "DosingRange",
    "SelectorCapacity",
    "SelectorSpeedProfile",
    # Aquaculture
    "FishCount",
    "FCR",
    # Log Entries
    "BiometryLogEntry",
    "MortalityLogEntry",
    "ConfigChangeLogEntry",
]
