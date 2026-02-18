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
        try:
            print("="*80)
            print("INICIANDO LIST_CAGES USE CASE")

            line_id_filter: Optional[LineId] = None
            if request.line_id:
                line_id_filter = LineId.from_string(request.line_id)

            print(f"Filtro line_id: {line_id_filter}")

            cages_with_info = await self._cage_repository.list_with_line_info(line_id=line_id_filter)
            print(f"Cages encontradas: {len(cages_with_info)}")

            cage_dtos = []
            for idx, (cage, line_name) in enumerate(cages_with_info):
                try:
                    print(f"Convirtiendo cage {idx}: {cage.name if hasattr(cage, 'name') else 'unknown'}")
                    dto = self._to_dto(cage, line_name)
                    cage_dtos.append(dto)
                except Exception as e:
                    import traceback
                    print(f"ERROR AL CONVERTIR CAGE {idx}:")
                    print(traceback.format_exc())
                    raise

            print(f"Total DTOs creados: {len(cage_dtos)}")
            result = ListCagesResponse(cages=cage_dtos)
            print("RESPONSE CREADA EXITOSAMENTE")
            print("="*80)
            return result
        except Exception as e:
            import traceback
            print("="*80)
            print("ERROR EN LIST_CAGES USE CASE:")
            print(traceback.format_exc())
            print("="*80)
            raise

    def _to_dto(self, cage, line_name: Optional[str]) -> CageListItemResponse:
        return CageListItemResponse(
            cage_id=str(cage.id),
            name=str(cage.name),
            line_id=str(cage.line_id) if cage.line_id else None,
            line_name=line_name,
            slot_number=cage.slot_number.value if cage.slot_number else None,
            current_fish_count=cage.current_fish_count.value if cage.current_fish_count else None,
            biomass_kg=cage.biomass.as_kg,
            avg_fish_weight_g=cage.avg_fish_weight.as_grams if cage.avg_fish_weight else None,
            created_at=cage.created_at,
            volume_m3=cage.total_volume.as_cubic_meters if cage.total_volume else None,
            max_density_kg_m3=float(cage.max_density) if cage.max_density else None,
            fcr=float(cage.fcr) if cage.fcr else None,
            feeding_table_id=str(cage.feeding_table_id) if cage.feeding_table_id else None,
            transport_time_seconds=cage.transport_time.value if cage.transport_time else None,
            status=cage.status.value
        )
