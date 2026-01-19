"""Use case para actualizar una jaula."""

from application.dtos.cage_dtos import (
    CageConfigResponse,
    CageResponse,
    UpdateCageRequest,
)
from domain.aggregates.cage import Cage
from domain.enums import CageStatus
from domain.repositories import ICageRepository
from domain.value_objects.identifiers import CageId
from domain.value_objects.names import CageName


class UpdateCageUseCase:
    """Caso de uso para actualizar nombre y/o status de una jaula."""

    def __init__(self, cage_repository: ICageRepository):
        self.cage_repository = cage_repository

    async def execute(self, cage_id: str, request: UpdateCageRequest) -> CageResponse:
        """
        Actualiza nombre y/o status de una jaula.

        Args:
            cage_id: ID de la jaula
            request: Datos a actualizar

        Returns:
            CageResponse con los datos actualizados

        Raises:
            ValueError: Si la jaula no existe o el nombre ya está en uso
        """
        cage = await self.cage_repository.find_by_id(CageId.from_string(cage_id))

        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Actualizar nombre si se proporciona
        if request.name is not None:
            new_name = CageName(request.name)

            # Verificar que no exista otra jaula con el mismo nombre
            existing = await self.cage_repository.find_by_name(new_name)
            if existing and existing.id != cage.id:
                raise ValueError(f"Ya existe otra jaula con el nombre '{request.name}'")

            cage.rename(new_name)

        # Actualizar status si se proporciona
        if request.status is not None:
            status_upper = request.status.upper()
            if status_upper == "AVAILABLE":
                cage.set_available()
            elif status_upper == "IN_USE":
                cage.set_in_use()
            elif status_upper == "MAINTENANCE":
                cage.set_maintenance()
            else:
                raise ValueError(
                    f"Status inválido: '{request.status}'. "
                    "Valores válidos: AVAILABLE, IN_USE, MAINTENANCE"
                )

        # Persistir cambios
        await self.cage_repository.save(cage)

        return self._to_response(cage)

    def _to_response(self, cage: Cage) -> CageResponse:
        """Convierte la entidad a response DTO."""
        return CageResponse(
            id=str(cage.id.value),
            name=str(cage.name),
            status=cage.status.value,
            created_at=cage.created_at,
            fish_count=cage.fish_count,
            avg_weight_grams=cage.avg_weight_grams,
            biomass_kg=cage.biomass_kg,
            config=CageConfigResponse(
                fcr=cage.config.fcr,
                volume_m3=cage.config.volume_m3,
                max_density_kg_m3=cage.config.max_density_kg_m3,
                transport_time_seconds=cage.config.transport_time_seconds,
            ),
            current_density_kg_m3=cage.current_density_kg_m3,
        )
