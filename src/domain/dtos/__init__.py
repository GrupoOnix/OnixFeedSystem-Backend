"""
DTOs del dominio de Feeding System.
"""

from .machine_io_v2 import (
    BlowerCommand,
    DoserCommand,
    MachineConfiguration,
    MachineStatus,
    SelectorCommand,
    SensorReading,
    SensorReadings,
)

__all__ = [
    "BlowerCommand",
    "DoserCommand",
    "MachineConfiguration",
    "MachineStatus",
    "SelectorCommand",
    "SensorReading",
    "SensorReadings",
]
