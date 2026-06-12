from typing import Optional
from domain.repositories import ICageRepository
from domain.value_objects import LineId
from application.dtos.cage_dtos import (
    ListCagesResponse,
    CageListItemResponse
)


class ListCagesRequest:
    """Request para listar jaulas."""

    def __init__(self, line_id: Optional[str] = None):
        self.line_id = line_id


class ListCagesUseCase:

    def __init__(self, cage_repository: ICageRepository):
        self._cage_repository = cage_repository

    async def execute(self, request: Optional[ListCagesRequest] = None) -> ListCagesResponse:
        try:
            print("="*80)
            print("INICIANDO LIST_CAGES USE CASE")

            line_id_filter: Optional[LineId] = None
            if request and request.line_id:
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
                except Exception:
                    import traceback
                    print(f"ERROR AL CONVERTIR CAGE {idx}:")
                    print(traceback.format_exc())
                    raise

            print(f"Total DTOs creados: {len(cage_dtos)}")
            result = ListCagesResponse(cages=cage_dtos, total=len(cage_dtos))
            print("RESPONSE CREADA EXITOSAMENTE")
            print("="*80)
            return result
        except Exception:
            import traceback
            print("="*80)
            print("ERROR EN LIST_CAGES USE CASE:")
            print(traceback.format_exc())
            print("="*80)
            raise

    def _to_dto(self, cage, line_name: Optional[str]) -> CageListItemResponse:
        from application.dtos.cage_dtos import CageConfigResponse
        return CageListItemResponse(
            id=str(cage.id),
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
            today_feeding_kg=0.0,
        )
