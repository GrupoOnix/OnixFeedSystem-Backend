from typing import List
from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.repositories import ISiloRepository, ICageRepository


class ResourceReleaser:
    """Libera recursos compartidos (silos y jaulas) de líneas de alimentación."""

    @staticmethod
    async def release_all_from_lines(
        lines: List[FeedingLine],
        silo_repo: ISiloRepository,
        cage_repo: ICageRepository
    ) -> None:
        """Libera todos los silos y jaulas de las líneas especificadas."""
        for line in lines:
            await ResourceReleaser._release_cages_from_line(line, cage_repo)
            await ResourceReleaser._release_silos_from_line(line, silo_repo)

    @staticmethod
    async def _release_cages_from_line(
        line: FeedingLine,
        cage_repo: ICageRepository
    ) -> None:
        """Libera todas las jaulas asignadas a una línea."""
        old_assignments = line.get_slot_assignments()
        for old_assignment in old_assignments:
            old_cage = await cage_repo.find_by_id(old_assignment.cage_id)
            if old_cage:
                # Cambiar estado a AVAILABLE
                # Las referencias line_id y slot_number se limpian en el repositorio
                from domain.enums import CageStatus
                old_cage.status = CageStatus.AVAILABLE
                await cage_repo.save(old_cage)

    @staticmethod
    async def _release_silos_from_line(
        line: FeedingLine,
        silo_repo: ISiloRepository
    ) -> None:
        """Libera todos los silos asignados a dosers de una línea."""
        for old_doser in line.dosers:
            old_silo = await silo_repo.find_by_id(old_doser.assigned_silo_id)
            if old_silo:
                old_silo.release_from_doser()
                await silo_repo.save(old_silo)
