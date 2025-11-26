from domain.repositories import IBiometryLogRepository
from domain.value_objects import CageId
from application.dtos.biometry_dtos import (
    BiometryLogItemResponse,
    PaginatedBiometryResponse,
    PaginationInfo
)


class ListBiometryUseCase:
    """
    Lista los registros de biometría de una jaula.
    
    Operación de solo lectura, no requiere transacción.
    """

    def __init__(self, biometry_log_repository: IBiometryLogRepository):
        self._biometry_log_repo = biometry_log_repository

    async def execute(self, cage_id: str, limit: int = 50, offset: int = 0) -> PaginatedBiometryResponse:
        """
        Ejecuta el listado paginado de registros de biometría.
        
        Args:
            cage_id: ID de la jaula
            limit: Cantidad máxima de registros a retornar
            offset: Cantidad de registros a saltar
            
        Returns:
            Respuesta paginada con registros de biometría ordenados por fecha DESC
        """
        cage_id_vo = CageId.from_string(cage_id)
        
        # Obtener registros del repositorio
        log_entries = await self._biometry_log_repo.list_by_cage(
            cage_id_vo,
            limit=limit,
            offset=offset
        )
        
        # Obtener total de registros
        total = await self._biometry_log_repo.count_by_cage(cage_id_vo)
        
        # Mapear a DTOs
        log_dtos = [
            BiometryLogItemResponse(
                biometry_id=str(entry.biometry_id),
                cage_id=str(entry.cage_id.value),
                old_fish_count=entry.old_fish_count,
                new_fish_count=entry.new_fish_count,
                old_average_weight_g=entry.old_average_weight_g,
                new_average_weight_g=entry.new_average_weight_g,
                sampling_date=entry.sampling_date,
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
        
        return PaginatedBiometryResponse(logs=log_dtos, pagination=pagination)
