from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from domain.value_objects import CageId


@dataclass(frozen=True)
class BiometryLogEntry:
    """
    Value Object que representa un registro de biometría.
    Inmutable, solo se crea y se consulta.
    """
    biometry_id: UUID
    cage_id: CageId
    old_fish_count: Optional[int]
    new_fish_count: Optional[int]
    old_average_weight_g: Optional[float]
    new_average_weight_g: Optional[float]
    sampling_date: date
    note: Optional[str]
    created_at: datetime

    @staticmethod
    def create(
        cage_id: CageId,
        old_fish_count: Optional[int],
        new_fish_count: Optional[int],
        old_average_weight_g: Optional[float],
        new_average_weight_g: Optional[float],
        sampling_date: date,
        note: Optional[str] = None,
    ) -> "BiometryLogEntry":
        """Factory method para crear un nuevo registro."""
        return BiometryLogEntry(
            biometry_id=uuid4(),
            cage_id=cage_id,
            old_fish_count=old_fish_count,
            new_fish_count=new_fish_count,
            old_average_weight_g=old_average_weight_g,
            new_average_weight_g=new_average_weight_g,
            sampling_date=sampling_date,
            note=note,
            created_at=datetime.utcnow(),
        )
