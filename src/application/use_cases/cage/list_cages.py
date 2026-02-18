"""Use case para listar jaulas."""

from typing import List, Optional

from application.dtos.cage_dtos import (
    CageConfigResponse,
    CageListItemResponse,
    ListCagesResponse,
)
from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository  # , IFeedingOperationRepository  # DEPRECATED
from domain.value_objects.identifiers import CageId


class ListCagesUseCase:
    """Caso de uso para listar todas las jaulas. DEPRECATED - uses old feeding system."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        operation_repository: Optional[object] = None,  # IFeedingOperationRepository - DEPRECATED
    ):
        self.cage_repository = cage_repository
        self.operation_repository = operation_repository

    async def execute(self) -> ListCagesResponse:
        """
        Lista todas las jaulas.

        Returns:
            ListCagesResponse con la lista de jaulas
        """
        cages = await self.cage_repository.list()

        # TODO: Recalcular today_feeding_kg desde FeedingSession/CageFeeding (Phase 5)
        # operation_repository fue removido al migrar al nuevo sistema de alimentación
        items = [self._to_list_item(cage, today_feeding_kg=0.0) for cage in cages]

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
