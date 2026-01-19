"""
Caso de Uso: Obtener Layout del Sistema

Responsabilidad:
- Cargar todos los agregados del sistema desde los repositorios
- Retornar entidades de dominio puras
"""

from typing import Dict, List, Tuple

from domain.aggregates.cage import Cage
from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.aggregates.silo import Silo
from domain.entities.slot_assignment import SlotAssignment
from domain.repositories import (
    ICageRepository,
    IFeedingLineRepository,
    ISiloRepository,
    ISlotAssignmentRepository,
)
from domain.value_objects import LineId


class GetSystemLayoutUseCase:
    """
    Caso de uso para obtener el layout completo del sistema.

    Carga todos los agregados desde los repositorios y los convierte
    a DTOs para ser consumidos por la capa de presentación.
    """

    def __init__(
        self,
        line_repo: IFeedingLineRepository,
        silo_repo: ISiloRepository,
        cage_repo: ICageRepository,
        slot_assignment_repo: ISlotAssignmentRepository,
    ):
        self.line_repo = line_repo
        self.silo_repo = silo_repo
        self.cage_repo = cage_repo
        self.slot_assignment_repo = slot_assignment_repo

    async def execute(
        self,
    ) -> Tuple[
        List[Silo], List[Cage], List[FeedingLine], Dict[LineId, List[SlotAssignment]]
    ]:
        """
        Ejecuta el caso de uso para obtener el layout del sistema.

        Returns:
            Tupla con (silos, cages, lines, slot_assignments_by_line)
        """
        # Cargar todos los agregados desde BD
        all_silos = await self.silo_repo.get_all()
        all_cages = await self.cage_repo.list()
        all_lines = await self.line_repo.get_all()

        # Cargar slot assignments agrupados por línea
        slot_assignments_by_line: Dict[LineId, List[SlotAssignment]] = {}
        for line in all_lines:
            assignments = await self.slot_assignment_repo.find_by_line(line.id)
            slot_assignments_by_line[line.id] = assignments

        return (all_silos, all_cages, all_lines, slot_assignments_by_line)
