from domain.repositories import IConfigChangeLogRepository
from domain.value_objects import CageId
from application.dtos.config_dtos import (
    ConfigChangeLogItemResponse,
    PaginatedConfigChangesResponse,
    PaginationInfo
)


class ListConfigChangesUseCase:
    """
    Lista los cambios de configuración de una jaula.
    
    Operación de solo lectura, no requiere transacción.
    """

    def __init__(self, config_change_log_repository: IConfigChangeLogRepository):
        self._config_log_repo = config_change_log_repository

    async def execute(self, cage_id: str, limit: int = 50, offset: int = 0) -> PaginatedConfigChangesResponse:
        """
        Ejecuta el listado paginado de cambios de configuración.
        
        Args:
            cage_id: ID de la jaula
            limit: Cantidad máxima de registros a retornar
            offset: Cantidad de registros a saltar
            
        Returns:
            Respuesta paginada con cambios de configuración ordenados por fecha DESC
        """
        cage_id_vo = CageId.from_string(cage_id)

        # Obtener registros del repositorio
        log_entries = await self._config_log_repo.list_by_cage(
            cage_id_vo,
            limit=limit,
            offset=offset
        )

        # Obtener total de registros
        total = await self._config_log_repo.count_by_cage(cage_id_vo)

        # Mapear a DTOs
        log_dtos = [
            ConfigChangeLogItemResponse(
                change_id=str(entry.change_id),
                cage_id=str(entry.cage_id.value),
                field_name=entry.field_name,
                old_value=entry.old_value,
                new_value=entry.new_value,
                change_reason=entry.change_reason,
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

        return PaginatedConfigChangesResponse(logs=log_dtos, pagination=pagination)
