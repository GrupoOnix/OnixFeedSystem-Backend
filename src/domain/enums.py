from enum import Enum


class CageStatus(Enum):
    AVAILABLE = "Disponible"
    IN_USE = "En Uso"
    MAINTENANCE = "Mantenimiento"


class SensorType(Enum):
    TEMPERATURE = "Temperatura"
    PRESSURE = "Presión"
    FLOW = "Caudal"

class DoserType(Enum):
    PULSE_DOSER = "PULSE_DOSER"
    VARI_DOSER = "VARI_DOSER"
    SCREW_DOSER = "SCREW_DOSER"