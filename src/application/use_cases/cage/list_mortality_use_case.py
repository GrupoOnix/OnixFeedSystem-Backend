from domain.repositories import IMortalityLogRepository
from domain.value_objects import CageId
from application.dtos.mortality_dtos import (
    MortalityLogItemResponse,
    PaginatedMortalityResponse,
    PaginationInfo
)


class ListMortalityUseCase:
    """
    Lista los registros de mortalidad de una jaula.
    
    Operación de solo lectura, no requiere transacción.
    """

    def __init__(self, mortality_log_repository: IMortalityLogRepository):
        self._mortality_log_repo = mortality_log_repository

    async def execute(self, cage_id: str, limit: int = 50, offset: int = 0) -> PaginatedMortalityResponse:
        """
        Ejecuta el listado paginado de registros de mortalidad.
        
        Args:
            cage_id: ID de la jaula
            limit: Cantidad máxima de registros a retornar
            offset: Cantidad de registros a saltar
            
        Returns:
            Respuesta paginada con registros de mortalidad ordenados por fecha DESC
        """
        cage_id_vo = CageId.from_string(cage_id)

        # Obtener registros del repositorio
        log_entries = await self._mortality_log_repo.list_by_cage(
            cage_id_vo,
            limit=limit,
            offset=offset
        )

        # Obtener total de registros
        total = await self._mortality_log_repo.count_by_cage(cage_id_vo)

        # Mapear a DTOs
        log_dtos = [
            MortalityLogItemResponse(
                mortality_id=str(entry.mortality_id),
                cage_id=str(entry.cage_id.value),
                dead_fish_count=entry.dead_fish_count,
                mortality_date=entry.mortality_date,
                note=entry.note,
                created_at=entry.created_at
            )
            for entry in log_entries
        ]

        # Calcular información de paginación
        has_next = (offset + limit) < total
        has_previous = offset > 0

        pagination = PaginationInfo(
            total=total,
            limit=limit,
            offset=offset,
            has_next=has_next,
            has_previous=has_previous
        )

        return PaginatedMortalityResponse(logs=log_dtos, pagination=pagination)
