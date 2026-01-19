"""Entidad que representa la asignación de una jaula a un slot de una línea."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from domain.value_objects.identifiers import CageId, LineId


@dataclass
class SlotAssignment:
    """
    Representa la asignación de una jaula a un slot específico
    en una línea de alimentación.

    Esta entidad maneja la relación entre:
    - FeedingLine (línea de alimentación)
    - Cage (jaula)
    - Slot number (posición física en el selector)
    """

    line_id: LineId
    cage_id: CageId
    slot_number: int
    id: UUID = None
    assigned_at: datetime = None

    def __post_init__(self) -> None:
        """Inicializa valores por defecto y valida."""
        if self.id is None:
            self.id = uuid4()
        if self.assigned_at is None:
            self.assigned_at = datetime.utcnow()

        if self.slot_number < 1:
            raise ValueError("El número de slot debe ser mayor o igual a 1")

    @classmethod
    def create(
        cls,
        line_id: LineId,
        cage_id: CageId,
        slot_number: int,
    ) -> "SlotAssignment":
        """Factory method para crear una nueva asignación."""
        return cls(
            line_id=line_id,
            cage_id=cage_id,
            slot_number=slot_number,
        )
