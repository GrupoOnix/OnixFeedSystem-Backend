from typing import List

from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.repositories import (
    ICageRepository,
    ISiloRepository,
    ISlotAssignmentRepository,
)
from domain.value_objects.identifiers import UserId


class ResourceReleaser:
    """Libera recursos compartidos (silos y jaulas) de líneas de alimentación."""

    @staticmethod
    async def release_all_from_lines(
        lines: List[FeedingLine],
        silo_repo: ISiloRepository,
        cage_repo: ICageRepository,
        slot_assignment_repo: ISlotAssignmentRepository,
        user_id: UserId,
    ) -> None:
        """Libera todos los silos y jaulas de las líneas especificadas."""
        for line in lines:
            await ResourceReleaser._release_cages_from_line(line, cage_repo, slot_assignment_repo, user_id)
            await ResourceReleaser._release_silos_from_line(line, silo_repo, user_id)

    @staticmethod
    async def _release_cages_from_line(
        line: FeedingLine,
        cage_repo: ICageRepository,
        slot_assignment_repo: ISlotAssignmentRepository,
        user_id: UserId,
    ) -> None:
        """Libera todas las jaulas asignadas a una línea."""
        # Obtener asignaciones de la línea
        assignments = await slot_assignment_repo.find_by_line(line.id, user_id)

        for assignment in assignments:
            # Obtener la jaula y cambiar su estado a AVAILABLE
            cage = await cage_repo.find_by_id(assignment.cage_id, user_id)
            if cage:
                cage.set_available()
                await cage_repo.save(cage)

        # Eliminar todas las asignaciones de la línea
        await slot_assignment_repo.delete_by_line(line.id, user_id)

    @staticmethod
    async def _release_silos_from_line(
        line: FeedingLine,
        silo_repo: ISiloRepository,
        user_id: UserId,
    ) -> None:
        """Libera todos los silos asignados a dosers de una línea."""
        for old_doser in line.dosers:
            old_silo = await silo_repo.find_by_id(old_doser.assigned_silo_id, user_id)
            if old_silo:
                old_silo.release_from_doser()
                await silo_repo.save(old_silo)
