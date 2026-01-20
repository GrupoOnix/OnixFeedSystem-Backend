"""Use case para crear un grupo de jaulas."""

from typing import List

from application.dtos.cage_group_dtos import (
    CageGroupMetricsResponse,
    CageGroupResponse,
    CreateCageGroupRequest,
)
from domain.aggregates.cage import Cage
from domain.aggregates.cage_group import CageGroup
from domain.repositories import ICageGroupRepository, ICageRepository
from domain.value_objects.identifiers import CageId


class CreateCageGroupUseCase:
    """Caso de uso para crear un nuevo grupo de jaulas."""

    def __init__(
        self,
        group_repository: ICageGroupRepository,
        cage_repository: ICageRepository,
    ):
        self.group_repository = group_repository
        self.cage_repository = cage_repository

    async def execute(self, request: CreateCageGroupRequest) -> CageGroupResponse:
        """
        Crea un nuevo grupo de jaulas.

        Args:
            request: Datos del grupo a crear

        Returns:
            CageGroupResponse con los datos del grupo creado

        Raises:
            ValueError: Si el nombre ya existe o si alguna jaula no existe
        """
        # 1. Validar que el nombre no exista (case-insensitive)
        if await self.group_repository.exists_by_name(request.name):
            raise ValueError(f"Ya existe un grupo con el nombre '{request.name}'")

        # 2. Validar que todas las jaulas existan
        await self._validate_cages_exist(request.cage_ids)

        # 3. Crear el aggregate root
        cage_group = CageGroup.create(
            name=request.name,
            cage_ids=request.cage_ids,
            description=request.description,
        )

        # 4. Persistir
        await self.group_repository.save(cage_group)

        # 5. Cargar jaulas para calcular métricas y retornar
        cages = await self._load_cages(cage_group.cage_ids)
        return self._to_response(cage_group, cages)

    async def _validate_cages_exist(self, cage_ids: List[str]) -> None:
        """
        Valida que todas las jaulas existan.

        Args:
            cage_ids: Lista de IDs de jaulas a validar

        Raises:
            ValueError: Si alguna jaula no existe
        """
        for cage_id_str in cage_ids:
            cage_id = CageId.from_string(cage_id_str)
            if not await self.cage_repository.exists(cage_id):
                raise ValueError(f"La jaula con ID '{cage_id_str}' no existe")

    async def _load_cages(self, cage_ids: List[CageId]) -> List[Cage]:
        """Carga las jaulas desde el repositorio."""
        cages = []
        for cage_id in cage_ids:
            cage = await self.cage_repository.find_by_id(cage_id)
            if cage:  # Ignorar jaulas que no existan (por si fueron eliminadas)
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
