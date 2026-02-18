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

# Log Entries (legacy - kept for backward compatibility)
from .biometry_log_entry import BiometryLogEntry

# Cage Configuration
from .cage_configuration import CageConfiguration
from .config_change_log_entry import ConfigChangeLogEntry

# Feeding Specs
from .feeding_specs import (
    BlowDurationInSeconds,
    BlowerPowerPercentage,
    CoolerPowerPercentage,
    DosingRange,
    DosingRate,
    SelectorCapacity,
    SelectorSpeedProfile,
)

# Feeding Rates
from .feeding_rates import CambioTasa, TasaAlimentacion
from .identifiers import (
    AlertId,
    BlowerId,
    CageGroupId,
    CageId,
    ComidaId,
    CoolerId,
    DoserId,
    FeedingTableId,
    FoodId,
    LineId,
    OperationId,
    ScheduledAlertId,
    SelectorId,
    SensorId,
    SessionId,
    SiloId,
    VisitaId,
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
    CageGroupName,
    CageName,
    CoolerName,
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
    "CageGroupId",
    "SiloId",
    "BlowerId",
    "CoolerId",
    "DoserId",
    "SelectorId",
    "SensorId",
    "FeedingTableId",
    "SessionId",
    "OperationId",
    "FoodId",
    "AlertId",
    "ScheduledAlertId",
    "ComidaId",
    "VisitaId",
    # Names
    "LineName",
    "CageName",
    "CageGroupName",
    "SiloName",
    "BlowerName",
    "CoolerName",
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
    "CoolerPowerPercentage",
    "DosingRate",
    "DosingRange",
    "SelectorCapacity",
    "SelectorSpeedProfile",
    # Feeding Rates
    "TasaAlimentacion",
    "CambioTasa",
    # Aquaculture
    "FishCount",
    "FCR",
    # Cage Configuration
    "CageConfiguration",
    # Log Entries (legacy)
    "BiometryLogEntry",
    "MortalityLogEntry",
    "ConfigChangeLogEntry",
]
