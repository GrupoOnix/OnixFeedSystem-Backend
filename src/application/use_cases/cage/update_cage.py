"""Use case para actualizar una jaula."""

from typing import Optional

from application.dtos.cage_dtos import (
    CageConfigResponse,
    CageResponse,
    UpdateCageRequest,
)
from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository  # , IFeedingOperationRepository  # DEPRECATED
from domain.value_objects.identifiers import CageId
from domain.value_objects.names import CageName


class UpdateCageUseCase:
    """Caso de uso para actualizar nombre y/o status de una jaula. DEPRECATED - uses old feeding system."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        operation_repository: Optional[object] = None,  # IFeedingOperationRepository - DEPRECATED
    ):
        self.cage_repository = cage_repository
        self.operation_repository = operation_repository

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
        cage_id_vo = CageId.from_string(cage_id)
        cage = await self.cage_repository.find_by_id(cage_id_vo)

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
                    f"Status inválido: '{request.status}'. Valores válidos: AVAILABLE, IN_USE, MAINTENANCE"
                )

        # Persistir cambios
        await self.cage_repository.save(cage)

        # Obtener alimentación del día
        today_feeding_kg = await self.operation_repository.get_today_dispensed_by_cage(cage_id_vo)

        return self._to_response(cage, today_feeding_kg)

    def _to_response(self, cage: Cage, today_feeding_kg: float = 0.0) -> CageResponse:
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
                blower_power=cage.config.blower_power,
                daily_feeding_target_kg=cage.config.daily_feeding_target_kg,
            ),
            current_density_kg_m3=cage.current_density_kg_m3,
            today_feeding_kg=today_feeding_kg,
        )
