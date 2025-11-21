from typing import Optional
from domain.repositories import ICageRepository
from domain.value_objects import LineId
from application.dtos.cage_dtos import (
    ListCagesRequest,
    ListCagesResponse,
    CageListItemResponse
)


class ListCagesUseCase:

    def __init__(self, cage_repository: ICageRepository):
        self._cage_repository = cage_repository
    
    async def execute(self, request: ListCagesRequest) -> ListCagesResponse:

        line_id_filter: Optional[LineId] = None
        if request.line_id:
            line_id_filter = LineId.from_string(request.line_id)
        
        cages_with_info = await self._cage_repository.list_with_line_info(line_id=line_id_filter)
        
        cage_dtos = [self._to_dto(cage, line_name) for cage, line_name in cages_with_info]
        
        return ListCagesResponse(cages=cage_dtos)
    
    def _to_dto(self, cage, line_name: Optional[str]) -> CageListItemResponse:
        return CageListItemResponse(
            cage_id=str(cage.id),
            name=str(cage.name),
            line_id=str(cage.line_id) if cage.line_id else None,
            line_name=line_name,
            slot_number=cage.slot_number.value if cage.slot_number else None,
            initial_fish_count=cage.initial_fish_count.value if cage.initial_fish_count else None,
            current_fish_count=cage.current_fish_count.value if cage.current_fish_count else None,
            biomass_kg=cage.biomass.as_kg,
            avg_fish_weight_g=cage.avg_fish_weight.as_grams if cage.avg_fish_weight else None
        )
