"""Use case para listar grupos de jaulas."""

from typing import List

from application.dtos.cage_group_dtos import (
    CageGroupMetricsResponse,
    CageGroupResponse,
    ListCageGroupsResponse,
)
from domain.aggregates.cage import Cage
from domain.aggregates.cage_group import CageGroup
from domain.repositories import ICageGroupRepository, ICageRepository
from domain.value_objects.identifiers import CageId


class ListCageGroupsUseCase:
    """Caso de uso para listar grupos de jaulas con filtros."""

    def __init__(
        self,
        group_repository: ICageGroupRepository,
        cage_repository: ICageRepository,
    ):
        self.group_repository = group_repository
        self.cage_repository = cage_repository

    async def execute(
        self,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ListCageGroupsResponse:
        """
        Lista grupos de jaulas con filtros opcionales.

        Args:
            search: Búsqueda en nombre, descripción o cage_ids (opcional)
            limit: Cantidad máxima de resultados (default 50)
            offset: Desplazamiento para paginación (default 0)

        Returns:
            ListCageGroupsResponse con los grupos y total
        """
        # 1. Obtener grupos con filtros
        groups = await self.group_repository.list(
            search=search, limit=limit, offset=offset
        )

        # 2. Contar total
        total = await self.group_repository.count(search=search)

        # 3. Convertir a response con métricas
        group_responses = []
        for group in groups:
            cages = await self._load_cages(group.cage_ids)
            group_responses.append(self._to_response(group, cages))

        return ListCageGroupsResponse(groups=group_responses, total=total)

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
