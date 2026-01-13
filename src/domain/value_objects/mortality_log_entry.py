from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from domain.value_objects.identifiers import CageId


@dataclass(frozen=True)
class MortalityLogEntry:
    """
    Value Object que representa un registro de mortalidad.
    Inmutable, solo se crea y se consulta.
    """

    mortality_id: UUID
    cage_id: CageId
    dead_fish_count: int
    mortality_date: date
    note: Optional[str]
    created_at: datetime

    @staticmethod
    def create(
        cage_id: CageId,
        dead_fish_count: int,
        mortality_date: date,
        note: Optional[str] = None,
    ) -> "MortalityLogEntry":
        """Factory method para crear un nuevo registro."""
        if dead_fish_count <= 0:
            raise ValueError("dead_fish_count debe ser mayor a 0")

        return MortalityLogEntry(
            mortality_id=uuid4(),
            cage_id=cage_id,
            dead_fish_count=dead_fish_count,
            mortality_date=mortality_date,
            note=note,
            created_at=datetime.utcnow(),
        )
