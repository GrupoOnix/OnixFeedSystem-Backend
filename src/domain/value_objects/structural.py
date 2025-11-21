"""
Value Objects estructurales y de relación.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .identifiers import CageId


@dataclass(frozen=True)
class SlotNumber:
    """Número de ranura (slot) con validación."""
    value: int

    def __post_init__(self):
        """Valida el número de ranura según las reglas de negocio."""
        if not isinstance(self.value, int):
            raise ValueError("El número de ranura debe ser un entero")
        
        if self.value < 1:
            raise ValueError("El número de ranura debe ser positivo (desde 1)")

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value
    
    def __hash__(self) -> int:
        return hash(self.value)


@dataclass(frozen=True)
class SlotAssignment:
    """
    Asignación de una jaula (CageId) a una ranura (SlotNumber) específica.
    
    Este VO representa la relación inmutable entre una ranura de la selectora
    y una jaula de destino, aplicando reglas de negocio en su creación.
    """
    slot_number: SlotNumber
    cage_id: CageId

    def __post_init__(self):
        """Valida la asignación de la ranura."""
        
        if not isinstance(self.slot_number, SlotNumber):
            raise ValueError("El número de ranura debe ser una instancia de SlotNumber")
        
        if not isinstance(self.cage_id, CageId):
            raise ValueError("El ID de jaula debe ser una instancia de CageId")

    def __str__(self) -> str:
        return f"Ranura {self.slot_number} -> Jaula {self.cage_id}"
    
    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: Any) -> bool:
        """Compara asignaciones por ranura y ID de jaula."""
        if not isinstance(other, SlotAssignment):
            return False
        return self.slot_number == other.slot_number and self.cage_id == other.cage_id

    def __hash__(self) -> int:
        """Genera hash para uso en sets y diccionarios."""
        return hash((self.slot_number, self.cage_id))
