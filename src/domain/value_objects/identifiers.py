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
    """Identificador único para una tabla de alimentación."""
    value: UUID

    @classmethod
    def generate(cls) -> FeedingTableId:
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> FeedingTableId:
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


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
