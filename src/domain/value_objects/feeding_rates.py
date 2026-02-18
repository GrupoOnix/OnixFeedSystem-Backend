"""
Value Objects para tasas de alimentación.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TasaAlimentacion:
    """
    Tasa de alimentación en kg/min.

    Representa la velocidad a la que se dispensa alimento.
    """

    kg_por_minuto: float

    def __post_init__(self):
        if not isinstance(self.kg_por_minuto, (int, float)):
            raise TypeError("La tasa debe ser un valor numérico")
        if self.kg_por_minuto <= 0:
            raise ValueError("La tasa debe ser mayor a 0 kg/min")

    def __str__(self) -> str:
        return f"{self.kg_por_minuto:.2f} kg/min"

    def __float__(self) -> float:
        return float(self.kg_por_minuto)


@dataclass(frozen=True)
class CambioTasa:
    """
    Registro de cambio de tasa durante una visita.

    Permite rastrear todos los ajustes de tasa en tiempo real.
    """

    timestamp: datetime
    tasa_anterior: TasaAlimentacion
    tasa_nueva: TasaAlimentacion
    operador_nombre: str

    def __post_init__(self):
        if not self.operador_nombre or not self.operador_nombre.strip():
            raise ValueError("El nombre del operador no puede estar vacío")
