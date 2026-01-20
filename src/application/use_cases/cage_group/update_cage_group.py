"""Use case para actualizar un grupo de jaulas."""

from typing import List

from application.dtos.cage_group_dtos import (
    CageGroupMetricsResponse,
    CageGroupResponse,
    UpdateCageGroupRequest,
)
from domain.aggregates.cage import Cage
from domain.aggregates.cage_group import CageGroup
from domain.repositories import ICageGroupRepository, ICageRepository
from domain.value_objects.identifiers import CageGroupId, CageId
from domain.value_objects.names import CageGroupName


class UpdateCageGroupUseCase:
    """Caso de uso para actualizar un grupo de jaulas."""

    def __init__(
        self,
        group_repository: ICageGroupRepository,
        cage_repository: ICageRepository,
    ):
        self.group_repository = group_repository
        self.cage_repository = cage_repository

    async def execute(
        self, group_id: str, request: UpdateCageGroupRequest
    ) -> CageGroupResponse:
        """
        Actualiza un grupo de jaulas.

        Args:
            group_id: ID del grupo a actualizar
            request: Datos a actualizar (nombre, descripción y/o cage_ids)

        Returns:
            CageGroupResponse con los datos actualizados

        Raises:
            ValueError: Si el grupo no existe, si el nombre ya existe o si alguna jaula no existe
        """
        # 1. Buscar el grupo
        group_id_obj = CageGroupId.from_string(group_id)
        group = await self.group_repository.find_by_id(group_id_obj)

        if not group:
            raise ValueError(f"No existe un grupo con ID '{group_id}'")

        # 2. Actualizar nombre si se proporciona
        if request.name is not None:
            # Validar que el nuevo nombre no exista (excepto el actual)
            if await self.group_repository.exists_by_name(
                request.name, exclude_id=group_id_obj
            ):
                raise ValueError(f"Ya existe un grupo con el nombre '{request.name}'")

            group.update_name(CageGroupName(request.name))

        # 3. Actualizar cage_ids si se proporciona
        if request.cage_ids is not None:
            # Validar que todas las jaulas existan
            await self._validate_cages_exist(request.cage_ids)

            # Convertir a CageId objects
            cage_id_objects = [CageId.from_string(id_str) for id_str in request.cage_ids]
            group.set_cages(cage_id_objects)

        # 4. Actualizar descripción si se proporciona (puede ser None para limpiarla)
        if request.description is not None:
            group.update_description(request.description)

        # 5. Persistir cambios
        await self.group_repository.save(group)

        # 6. Cargar jaulas y retornar
        cages = await self._load_cages(group.cage_ids)
        return self._to_response(group, cages)

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
