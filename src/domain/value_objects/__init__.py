"""
Value Objects del dominio de Feeding System.

Este módulo centraliza todos los Value Objects organizados por categoría.
Los imports se mantienen simples desde fuera del módulo:

    from domain.value_objects import CageId, FishCount, Weight
"""

# Identifiers
from .identifiers import (
    LineId,
    CageId,
    SiloId,
    BlowerId,
    DoserId,
    SelectorId,
    SensorId,
    FeedingTableId,
)

# Names
from .names import (
    LineName,
    CageName,
    SiloName,
    BlowerName,
    DoserName,
    SelectorName,
    SensorName,
)

# Measurements
from .measurements import (
    Weight,
    Volume,
    Density,
)

# Feeding Specs
from .feeding_specs import (
    BlowerPowerPercentage,
    BlowDurationInSeconds,
    DosingRate,
    DosingRange,
    SelectorCapacity,
    SelectorSpeedProfile,
)

# Aquaculture
from .aquaculture import (
    FishCount,
    FCR,
)

# Structural
from .structural import (
    SlotNumber,
    SlotAssignment,
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
    # Names
    "LineName",
    "CageName",
    "SiloName",
    "BlowerName",
    "DoserName",
    "SelectorName",
    "SensorName",
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
    # Structural
    "SlotNumber",
    "SlotAssignment",
]
