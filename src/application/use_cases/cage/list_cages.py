"""Use case para listar jaulas."""

from application.dtos.cage_dtos import (
    CageConfigResponse,
    CageListItemResponse,
    ListCagesResponse,
)
from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository, ICageFeedingRepository
from domain.value_objects.identifiers import UserId


class ListCagesUseCase:
    """Caso de uso para listar todas las jaulas."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        cage_feeding_repository: ICageFeedingRepository,
    ):
        self.cage_repository = cage_repository
        self.cage_feeding_repository = cage_feeding_repository

    async def execute(self, user_id: UserId) -> ListCagesResponse:
        """
        Lista todas las jaulas de un usuario.

        Args:
            user_id: ID del usuario propietario

        Returns:
            ListCagesResponse con la lista de jaulas
        """
        cages = await self.cage_repository.list(user_id)

        cage_ids = [str(cage.id.value) for cage in cages]
        dispensed_map = await self.cage_feeding_repository.get_today_dispensed_by_cages(cage_ids)
        items = [
            self._to_list_item(cage, today_feeding_kg=dispensed_map.get(str(cage.id.value), 0.0)) for cage in cages
        ]

        return ListCagesResponse(cages=items, total=len(items))

    def _to_list_item(self, cage: Cage, today_feeding_kg: float = 0.0) -> CageListItemResponse:
        """Convierte la entidad a item de lista."""
        return CageListItemResponse(
            id=str(cage.id.value),
            name=str(cage.name),
            status=cage.status.value,
            fish_count=cage.fish_count,
            avg_weight_grams=cage.avg_weight_grams,
            biomass_kg=cage.biomass_kg,
            created_at=cage.created_at,
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
