"""Use case para actualizar la configuración de una jaula."""

from application.dtos.cage_dtos import (
    CageConfigResponse,
    CageResponse,
    UpdateCageConfigRequest,
)
from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository
from domain.value_objects.cage_configuration import CageConfiguration
from domain.value_objects.identifiers import CageId


class UpdateCageConfigUseCase:
    """Caso de uso para actualizar la configuración de una jaula."""

    def __init__(self, cage_repository: ICageRepository):
        self.cage_repository = cage_repository

    async def execute(
        self, cage_id: str, request: UpdateCageConfigRequest
    ) -> CageResponse:
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
        cage = await self.cage_repository.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Construir nueva configuración preservando valores existentes
        current_config = cage.config

        new_config = CageConfiguration(
            fcr=request.fcr if request.fcr is not None else current_config.fcr,
            volume_m3=request.volume_m3
            if request.volume_m3 is not None
            else current_config.volume_m3,
            max_density_kg_m3=request.max_density_kg_m3
            if request.max_density_kg_m3 is not None
            else current_config.max_density_kg_m3,
            transport_time_seconds=request.transport_time_seconds
            if request.transport_time_seconds is not None
            else current_config.transport_time_seconds,
            blower_power=request.blower_power
            if request.blower_power is not None
            else current_config.blower_power,
        )

        # Actualizar configuración
        cage.update_config(new_config)

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
                blower_power=cage.config.blower_power,
            ),
            current_density_kg_m3=cage.current_density_kg_m3,
        )
