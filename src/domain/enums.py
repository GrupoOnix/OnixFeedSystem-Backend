from enum import Enum


class CageStatus(Enum):
    AVAILABLE = "Disponible"
    IN_USE = "En Uso"
    MAINTENANCE = "Mantenimiento"