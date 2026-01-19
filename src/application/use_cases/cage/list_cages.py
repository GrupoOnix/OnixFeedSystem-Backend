"""Use case para listar jaulas."""

from application.dtos.cage_dtos import (
    CageListItemResponse,
    ListCagesResponse,
)
from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository


class ListCagesUseCase:
    """Caso de uso para listar todas las jaulas."""

    def __init__(self, cage_repository: ICageRepository):
        self.cage_repository = cage_repository

    async def execute(self) -> ListCagesResponse:
        """
        Lista todas las jaulas.

        Returns:
            ListCagesResponse con la lista de jaulas
        """
        cages = await self.cage_repository.list()

        items = [self._to_list_item(cage) for cage in cages]

        return ListCagesResponse(cages=items, total=len(items))

    def _to_list_item(self, cage: Cage) -> CageListItemResponse:
        """Convierte la entidad a item de lista."""
        return CageListItemResponse(
            id=str(cage.id.value),
            name=str(cage.name),
            status=cage.status.value,
            fish_count=cage.fish_count,
            avg_weight_grams=cage.avg_weight_grams,
            biomass_kg=cage.biomass_kg,
            created_at=cage.created_at,
        )
