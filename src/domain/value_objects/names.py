"""
Value Objects para nombres de entidades.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._validators import validate_name_format


@dataclass(frozen=True)
class LineName:
    """Nombre de una línea de alimentación con reglas de validación."""

    value: str

    def __post_init__(self):
        """Valida el nombre de línea según las reglas de negocio."""
        validate_name_format(self.value, "El nombre de línea")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class BlowerName:
    """Nombre de un componente soplador con validación."""

    value: str

    def __post_init__(self):
        """Valida el nombre del soplador según las reglas de negocio."""
        validate_name_format(self.value, "El nombre del soplador")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DoserName:
    """Nombre de un componente dosificador con validación."""

    value: str

    def __post_init__(self):
        """Valida el nombre del dosificador según las reglas de negocio."""
        validate_name_format(self.value, "El nombre del dosificador")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SelectorName:
    """Nombre de un componente selector con validación."""

    value: str

    def __post_init__(self):
        """Valida el nombre del selector según las reglas de negocio."""
        validate_name_format(self.value, "El nombre del selector")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SensorName:
    """Nombre de un sensor con validación."""

    value: str

    def __post_init__(self):
        validate_name_format(self.value, "El nombre del sensor")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CageName:
    """Nombre de una jaula con validación."""

    value: str

    def __post_init__(self):
        validate_name_format(self.value, "El nombre de la jaula")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CageGroupName:
    """Nombre de un grupo de jaulas con validación."""

    value: str

    def __post_init__(self):
        validate_name_format(self.value, "El nombre del grupo de jaulas")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SiloName:
    """Nombre de un silo con validación."""

    value: str

    def __post_init__(self):
        validate_name_format(self.value, "El nombre del silo")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class FoodName:
    """Nombre de un alimento con validación."""

    value: str

    def __post_init__(self):
        validate_name_format(self.value, "El nombre del alimento")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CoolerName:
    """Nombre de un cooler (enfriador de aire) con validación."""

    value: str

    def __post_init__(self):
        validate_name_format(self.value, "El nombre del cooler")

    def __str__(self) -> str:
        return self.value
