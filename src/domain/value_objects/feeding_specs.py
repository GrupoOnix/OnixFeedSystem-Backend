"""
Value Objects para especificaciones de alimentación y componentes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BlowerPowerPercentage:
    """
    Representa la potencia del soplador como un valor porcentual (0-100).
    Este es el valor que el software maneja y que el PLC interpretará.
    """

    value: float

    def __post_init__(self):
        """Valida que el valor sea un porcentaje válido (0-100)."""

        if not isinstance(self.value, (int, float)):
            raise ValueError("La potencia (porcentaje) debe ser un valor numérico")

        # Regla de negocio: El valor debe estar entre 0% y 100%
        if not 0.0 <= self.value <= 100.0:
            raise ValueError("La potencia debe ser un porcentaje entre 0.0 y 100.0")

    def __str__(self) -> str:
        return f"{self.value} %"


@dataclass(frozen=True)
class BlowDurationInSeconds:
    """
    Representa un tiempo/duración de soplado en segundos.
    Usado para 'soplado antes' y 'soplado después'.
    """

    value: int

    def __post_init__(self):
        """Valida que la duración sea un número razonable."""

        if not isinstance(self.value, int):
            raise ValueError("La duración de soplado debe ser un entero (en segundos)")

        if self.value < 0:
            raise ValueError("La duración de soplado no puede ser negativa")

        if self.value > 600:
            raise ValueError(
                "La duración de soplado no puede exceder 600 segundos (10 minutos)"
            )

    def __str__(self) -> str:
        return f"{self.value} s"


@dataclass(frozen=True)
class DosingRate:
    """Tasa de dosificación para componentes dosificadores con validación."""

    value: float
    unit: str = "kg/min"

    def __post_init__(self):
        """Valida la tasa de dosificación según las reglas de negocio."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("La tasa de dosificación debe ser un valor numérico")

        if self.value < 0:
            raise ValueError("La tasa de dosificación no puede ser negativa")

        if self.value > 1000:
            raise ValueError("La tasa de dosificación no puede exceder 1000 kg/min")

        if not isinstance(self.unit, str) or not self.unit:
            raise ValueError(
                "La unidad de tasa de dosificación debe ser una cadena no vacía"
            )

    def __str__(self) -> str:
        return f"{self.value} {self.unit}"


@dataclass(frozen=True)
class DosingRange:
    """Rango de tasas de dosificación válidas con validación."""

    min_rate: float
    max_rate: float
    unit: str = "kg/min"

    def __post_init__(self):
        """Valida el rango de dosificación según las reglas de negocio."""
        if not isinstance(self.min_rate, (int, float)):
            raise ValueError(
                "La tasa mínima de dosificación debe ser un valor numérico"
            )

        if not isinstance(self.max_rate, (int, float)):
            raise ValueError(
                "La tasa máxima de dosificación debe ser un valor numérico"
            )

        if self.min_rate < 0:
            raise ValueError("La tasa mínima de dosificación no puede ser negativa")

        if self.max_rate < 0:
            raise ValueError("La tasa máxima de dosificación no puede ser negativa")

        if self.min_rate >= self.max_rate:
            raise ValueError("La tasa mínima debe ser menor que la tasa máxima")

        if not isinstance(self.unit, str) or not self.unit:
            raise ValueError(
                "La unidad del rango de dosificación debe ser una cadena no vacía"
            )

    def contains(self, rate: DosingRate) -> bool:
        """Verifica si una tasa de dosificación está dentro de este rango."""
        if rate.unit != self.unit:
            raise ValueError(
                f"La unidad de tasa '{rate.unit}' no coincide con la unidad del rango '{self.unit}'"
            )

        return self.min_rate <= rate.value <= self.max_rate

    def __str__(self) -> str:
        return f"{self.min_rate}-{self.max_rate} {self.unit}"


@dataclass(frozen=True)
class SelectorCapacity:
    """Capacidad (número de ranuras) para un componente selector."""

    value: int

    def __post_init__(self):
        """Valida la capacidad del selector."""
        if not isinstance(self.value, int):
            raise ValueError("La capacidad del selector debe ser un entero")

        if self.value <= 0:
            raise ValueError("La capacidad del selector debe ser mayor que 0")

    def __str__(self) -> str:
        return f"{self.value} ranuras"


@dataclass(frozen=True)
class SelectorSpeedProfile:
    """
    Encapsula la configuración de velocidad para una Selectora.

    Reutiliza el VO BlowerPowerPercentage para validar que las
    velocidades estén entre 0-100.
    """

    fast_speed: BlowerPowerPercentage
    slow_speed: BlowerPowerPercentage

    def __post_init__(self):
        """Valida reglas de negocio del perfil de velocidad."""
        if self.slow_speed.value >= self.fast_speed.value:
            raise ValueError(
                "La velocidad lenta debe ser menor que la velocidad rápida."
            )

    def __str__(self) -> str:
        return f"Fast: {self.fast_speed}, Slow: {self.slow_speed}"


@dataclass(frozen=True)
class CoolerPowerPercentage:
    """
    Potencia de enfriamiento del cooler como valor porcentual (0-100).
    Representa el porcentaje de capacidad de enfriamiento aplicado.
    """

    value: float

    def __post_init__(self):
        """Valida que el valor sea un porcentaje válido (0-100)."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("La potencia de enfriamiento debe ser un valor numérico")

        if not 0.0 <= self.value <= 100.0:
            raise ValueError(
                "La potencia de enfriamiento debe ser un porcentaje entre 0.0 y 100.0"
            )

    def __str__(self) -> str:
        return f"{self.value} %"
