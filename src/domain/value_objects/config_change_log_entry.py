from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from domain.value_objects.identifiers import CageId


@dataclass(frozen=True)
class ConfigChangeLogEntry:
    """
    Value Object que representa un cambio de configuración en una jaula.
    Inmutable, solo se crea y se consulta.
    """

    change_id: UUID
    cage_id: CageId
    field_name: str
    old_value: str
    new_value: str
    change_reason: Optional[str]
    created_at: datetime

    @staticmethod
    def create(
        cage_id: CageId,
        field_name: str,
        old_value: str,
        new_value: str,
        change_reason: Optional[str] = None,
    ) -> "ConfigChangeLogEntry":
        """Factory method para crear un nuevo registro de cambio."""
        if old_value == new_value:
            raise ValueError(
                f"No se puede crear log de cambio: old_value == new_value para campo '{field_name}'"
            )

        return ConfigChangeLogEntry(
            change_id=uuid4(),
            cage_id=cage_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            change_reason=change_reason,
            created_at=datetime.utcnow(),
        )
