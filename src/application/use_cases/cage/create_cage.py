"""Use case para crear una jaula."""

from application.dtos.cage_dtos import (
    CageConfigResponse,
    CageResponse,
    CreateCageRequest,
)
from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository
from domain.value_objects.cage_configuration import CageConfiguration
from domain.value_objects.names import CageName


class CreateCageUseCase:
    """Caso de uso para crear una nueva jaula."""

    def __init__(self, cage_repository: ICageRepository):
        self.cage_repository = cage_repository

    async def execute(self, request: CreateCageRequest) -> CageResponse:
        """
        Crea una nueva jaula.

        Args:
            request: Datos para crear la jaula

        Returns:
            CageResponse con los datos de la jaula creada

        Raises:
            ValueError: Si ya existe una jaula con ese nombre
        """
        # Verificar que no exista una jaula con el mismo nombre
        cage_name = CageName(request.name)
        existing = await self.cage_repository.find_by_name(cage_name)
        if existing:
            raise ValueError(f"Ya existe una jaula con el nombre '{request.name}'")

        # Crear configuración
        config = CageConfiguration(
            fcr=request.fcr,
            volume_m3=request.volume_m3,
            max_density_kg_m3=request.max_density_kg_m3,
            transport_time_seconds=request.transport_time_seconds,
            blower_power=request.blower_power,
        )

        # Crear jaula
        cage = Cage(name=cage_name, config=config)

        # Persistir
        await self.cage_repository.save(cage)

        # Retornar response
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
                daily_feeding_target_kg=cage.config.daily_feeding_target_kg,
            ),
            current_density_kg_m3=cage.current_density_kg_m3,
            today_feeding_kg=0.0,  # Nueva jaula, sin alimentación aún
        )
