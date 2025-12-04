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
        # Obtener cages directamente del repositorio
        cages = await cage_repo.find_by_line_id(line.id)

        for cage in cages:
            # Usar método de dominio para desasignar
            cage.unassign_from_line()

            # Cambiar estado a AVAILABLE
            from domain.enums import CageStatus
            cage.status = CageStatus.AVAILABLE

            await cage_repo.save(cage)

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
