"""Use case para obtener un grupo de jaulas por ID."""

from typing import List

from application.dtos.cage_group_dtos import (
    CageGroupMetricsResponse,
    CageGroupResponse,
)
from domain.aggregates.cage import Cage
from domain.aggregates.cage_group import CageGroup
from domain.repositories import ICageGroupRepository, ICageRepository
from domain.value_objects.identifiers import CageGroupId, CageId


class GetCageGroupUseCase:
    """Caso de uso para obtener un grupo de jaulas por ID."""

    def __init__(
        self,
        group_repository: ICageGroupRepository,
        cage_repository: ICageRepository,
    ):
        self.group_repository = group_repository
        self.cage_repository = cage_repository

    async def execute(self, group_id: str) -> CageGroupResponse:
        """
        Obtiene un grupo de jaulas por su ID.

        Args:
            group_id: ID del grupo

        Returns:
            CageGroupResponse con los datos del grupo

        Raises:
            ValueError: Si el grupo no existe
        """
        # 1. Buscar el grupo
        group = await self.group_repository.find_by_id(
            CageGroupId.from_string(group_id)
        )

        if not group:
            raise ValueError(f"No existe un grupo con ID '{group_id}'")

        # 2. Cargar jaulas y calcular métricas
        cages = await self._load_cages(group.cage_ids)

        return self._to_response(group, cages)

    async def _load_cages(self, cage_ids: List[CageId]) -> List[Cage]:
        """Carga las jaulas desde el repositorio."""
        cages = []
        for cage_id in cage_ids:
            cage = await self.cage_repository.find_by_id(cage_id)
            if cage:  # Ignorar jaulas que no existan
                cages.append(cage)
        return cages

    def _to_response(
        self, cage_group: CageGroup, cages: List[Cage]
    ) -> CageGroupResponse:
        """Convierte la entidad a response DTO."""
        metrics = cage_group.calculate_metrics(cages)

        return CageGroupResponse(
            id=str(cage_group.id.value),
            name=str(cage_group.name),
            description=cage_group.description,
            cage_ids=[str(cage_id.value) for cage_id in cage_group.cage_ids],
            created_at=cage_group.created_at,
            updated_at=cage_group.updated_at,
            metrics=CageGroupMetricsResponse(
                total_population=metrics.total_population,
                total_biomass=metrics.total_biomass,
                avg_weight=metrics.avg_weight,
                total_volume=metrics.total_volume,
                avg_density=metrics.avg_density,
            ),
        )
