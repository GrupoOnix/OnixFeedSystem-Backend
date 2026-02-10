"""Use case para actualizar la configuración de una jaula."""

from application.dtos.cage_dtos import (
    CageConfigResponse,
    CageResponse,
    UpdateCageConfigRequest,
)
from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository, IFeedingOperationRepository
from domain.value_objects.cage_configuration import CageConfiguration
from domain.value_objects.identifiers import CageId


class UpdateCageConfigUseCase:
    """Caso de uso para actualizar la configuración de una jaula."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        operation_repository: IFeedingOperationRepository,
    ):
        self.cage_repository = cage_repository
        self.operation_repository = operation_repository

    async def execute(self, cage_id: str, request: UpdateCageConfigRequest) -> CageResponse:
        """
        Actualiza la configuración de una jaula.

        Solo actualiza los campos proporcionados, manteniendo los demás.

        Args:
            cage_id: ID de la jaula
            request: Configuración a actualizar

        Returns:
            CageResponse con los datos actualizados

        Raises:
            ValueError: Si la jaula no existe
        """
        cage_id_vo = CageId.from_string(cage_id)
        cage = await self.cage_repository.find_by_id(cage_id_vo)
        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Construir nueva configuración preservando valores existentes
        current_config = cage.config

        new_config = CageConfiguration(
            fcr=request.fcr if request.fcr is not None else current_config.fcr,
            volume_m3=request.volume_m3 if request.volume_m3 is not None else current_config.volume_m3,
            max_density_kg_m3=request.max_density_kg_m3
            if request.max_density_kg_m3 is not None
            else current_config.max_density_kg_m3,
            transport_time_seconds=request.transport_time_seconds
            if request.transport_time_seconds is not None
            else current_config.transport_time_seconds,
            blower_power=request.blower_power if request.blower_power is not None else current_config.blower_power,
            daily_feeding_target_kg=request.daily_feeding_target_kg
            if request.daily_feeding_target_kg is not None
            else current_config.daily_feeding_target_kg,
        )

        # Actualizar configuración
        cage.update_config(new_config)

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
