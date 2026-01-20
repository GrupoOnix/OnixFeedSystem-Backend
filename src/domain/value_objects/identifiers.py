"""
Value Objects para identificadores únicos (IDs).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

# ============================================================================
# Identificadores de Aggregate Roots
# ============================================================================


@dataclass(frozen=True)
class LineId:
    """Identificador único para una línea de alimentación."""

    value: UUID

    @classmethod
    def generate(cls) -> LineId:
        """Genera un nuevo LineId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> LineId:
        """Crea un LineId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class CageId:
    """Identificador único para una jaula."""

    value: UUID

    @classmethod
    def generate(cls) -> CageId:
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> CageId:
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class CageGroupId:
    """Identificador único para un grupo de jaulas."""

    value: UUID

    @classmethod
    def generate(cls) -> CageGroupId:
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> CageGroupId:
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class SiloId:
    """Identificador único para un silo."""

    value: UUID

    @classmethod
    def generate(cls) -> SiloId:
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> SiloId:
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class FeedingTableId:
    """
    Identificador para una tabla de alimentación.
    Usa string simple en lugar de UUID para permitir IDs descriptivos
    como 'table-premium-2024', 'winter-table', etc.
    """

    value: str

    def __post_init__(self):
        """Valida que el ID no esté vacío."""
        if not self.value or not self.value.strip():
            raise ValueError("FeedingTableId no puede estar vacío")

    @classmethod
    def from_string(cls, id_str: str) -> FeedingTableId:
        """Crea un FeedingTableId desde una cadena."""
        return cls(id_str)

    def __str__(self) -> str:
        return self.value


# ============================================================================
# Identificadores de Entidades Hijas
# ============================================================================


@dataclass(frozen=True)
class BlowerId:
    """Identificador único para una entidad soplador."""

    value: UUID

    @classmethod
    def generate(cls) -> BlowerId:
        """Genera un nuevo BlowerId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> BlowerId:
        """Crea un BlowerId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class DoserId:
    """Identificador único para una entidad dosificador."""

    value: UUID

    @classmethod
    def generate(cls) -> DoserId:
        """Genera un nuevo DoserId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> DoserId:
        """Crea un DoserId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class SelectorId:
    """Identificador único para una entidad selector."""

    value: UUID

    @classmethod
    def generate(cls) -> SelectorId:
        """Genera un nuevo SelectorId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> SelectorId:
        """Crea un SelectorId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class SensorId:
    """Identificador único para una entidad sensor."""

    value: UUID

    @classmethod
    def generate(cls) -> SensorId:
        """Genera un nuevo SensorId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> SensorId:
        """Crea un SensorId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class SessionId:
    """Identificador único para una sesión de alimentación."""

    value: UUID

    @classmethod
    def generate(cls) -> SessionId:
        """Genera un nuevo SessionId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> SessionId:
        """Crea un SessionId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class OperationId:
    """Identificador único para una operación de alimentación."""

    value: UUID

    @classmethod
    def generate(cls) -> OperationId:
        """Genera un nuevo OperationId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> OperationId:
        """Crea un OperationId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class FoodId:
    """Identificador único para un alimento."""

    value: UUID

    @classmethod
    def generate(cls) -> FoodId:
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> FoodId:
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


# ============================================================================
# Identificadores de Alertas
# ============================================================================


@dataclass(frozen=True)
class AlertId:
    """Identificador único para una alerta."""

    value: UUID

    @classmethod
    def generate(cls) -> AlertId:
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> AlertId:
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ScheduledAlertId:
    """Identificador único para una alerta programada."""

    value: UUID

    @classmethod
    def generate(cls) -> ScheduledAlertId:
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> ScheduledAlertId:
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


# ============================================================================
# Identificadores de Componentes de Línea
# ============================================================================


@dataclass(frozen=True)
class CoolerId:
    """Identificador único para un cooler (enfriador de aire)."""

    value: UUID

    @classmethod
    def generate(cls) -> CoolerId:
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> CoolerId:
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)
