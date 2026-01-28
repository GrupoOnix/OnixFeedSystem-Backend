"""Use case para obtener una jaula."""

from application.dtos.cage_dtos import CageConfigResponse, CageResponse
from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository
from domain.value_objects.identifiers import CageId


class GetCageUseCase:
    """Caso de uso para obtener una jaula por ID."""

    def __init__(self, cage_repository: ICageRepository):
        self.cage_repository = cage_repository

    async def execute(self, cage_id: str) -> CageResponse:
        """
        Obtiene una jaula por su ID.

        Args:
            cage_id: ID de la jaula

        Returns:
            CageResponse con los datos de la jaula

        Raises:
            ValueError: Si la jaula no existe
        """
        cage = await self.cage_repository.find_by_id(CageId.from_string(cage_id))

        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

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
