"""
Value Objects específicos del dominio de acuicultura.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class FishCount:
    """Cantidad de peces en una jaula."""
    value: int

    def __post_init__(self):
        if not isinstance(self.value, int):
            raise TypeError("La cantidad de peces debe ser un entero")
        
        if self.value < 0:
            raise ValueError("La cantidad de peces no puede ser negativa")

    def __str__(self) -> str:
        return f"{self.value} peces"

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True)
class FCR:
    """
    Feed Conversion Ratio - Factor de conversión alimenticia.
    Indica cuántos kg de alimento se necesitan para producir 1 kg de biomasa.
    """
    value: float

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise TypeError("El FCR debe ser un valor numérico")
        
        if self.value < 0.5:
            raise ValueError("El FCR no puede ser menor a 0.5")
        
        if self.value > 3.0:
            raise ValueError("El FCR no puede exceder 3.0")

    def __str__(self) -> str:
        return f"{self.value:.2f}"

    def __float__(self) -> float:
        return float(self.value)
