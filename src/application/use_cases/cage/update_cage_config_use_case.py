from typing import List

from domain.repositories import ICageRepository, IConfigChangeLogRepository
from domain.value_objects import CageId, FCR, Volume, Density, FeedingTableId, BlowDurationInSeconds
from domain.value_objects.config_change_log_entry import ConfigChangeLogEntry
from application.dtos.config_dtos import UpdateCageConfigRequest


class UpdateCageConfigUseCase:
    """
    Actualiza la configuración de una jaula y registra los cambios.
    
    Solo crea logs para campos que realmente cambian (OLD != NEW).
    
    Patrón transaccional:
    - Si cualquier operación falla, toda la transacción se revierte
    - No hay commits explícitos, SQLAlchemy maneja la transacción
    """

    def __init__(
        self,
        cage_repository: ICageRepository,
        config_change_log_repository: IConfigChangeLogRepository
    ):
        self._cage_repo = cage_repository
        self._config_log_repo = config_change_log_repository

    async def execute(self, cage_id: str, request: UpdateCageConfigRequest) -> None:
        """
        Ejecuta la actualización de configuración.
        
        Args:
            cage_id: ID de la jaula
            request: Datos de configuración a actualizar
            
        Raises:
            ValueError: Si la jaula no existe o hay errores de validación
        """
        # Obtener jaula
        cage = await self._cage_repo.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"La jaula con ID '{cage_id}' no existe")
        
        # Lista para almacenar cambios
        changes: List[ConfigChangeLogEntry] = []
        
        # Procesar cada campo opcional
        if request.fcr is not None:
            old_value = str(cage.fcr.value) if cage.fcr else "None"
            new_fcr = FCR(request.fcr)  # Validación en el VO
            new_value = str(new_fcr.value)
            
            if old_value != new_value:
                cage.fcr = new_fcr
                changes.append(ConfigChangeLogEntry.create(
                    cage_id=cage.id,
                    field_name="fcr",
                    old_value=old_value,
                    new_value=new_value,
                    change_reason=request.change_reason
                ))
        
        if request.volume_m3 is not None:
            old_value = str(cage.total_volume.as_cubic_meters) if cage.total_volume else "None"
            new_volume = Volume.from_cubic_meters(request.volume_m3)  # Validación en el VO
            new_value = str(new_volume.as_cubic_meters)
            
            if old_value != new_value:
                cage.total_volume = new_volume
                changes.append(ConfigChangeLogEntry.create(
                    cage_id=cage.id,
                    field_name="volume_m3",
                    old_value=old_value,
                    new_value=new_value,
                    change_reason=request.change_reason
                ))
        
        if request.max_density_kg_m3 is not None:
            old_value = str(cage.max_density.value) if cage.max_density else "None"
            new_density = Density(request.max_density_kg_m3)  # Validación en el VO
            new_value = str(new_density.value)
            
            if old_value != new_value:
                cage.max_density = new_density
                changes.append(ConfigChangeLogEntry.create(
                    cage_id=cage.id,
                    field_name="max_density_kg_m3",
                    old_value=old_value,
                    new_value=new_value,
                    change_reason=request.change_reason
                ))
        
        if request.feeding_table_id is not None:
            old_value = str(cage.feeding_table_id.value) if cage.feeding_table_id else "None"
            new_table_id = FeedingTableId(request.feeding_table_id)  # Validación en el VO
            new_value = str(new_table_id.value)
            
            if old_value != new_value:
                cage.feeding_table_id = new_table_id
                changes.append(ConfigChangeLogEntry.create(
                    cage_id=cage.id,
                    field_name="feeding_table_id",
                    old_value=old_value,
                    new_value=new_value,
                    change_reason=request.change_reason
                ))
        
        if request.transport_time_seconds is not None:
            old_value = str(cage.transport_time.value) if cage.transport_time else "None"
            new_time = BlowDurationInSeconds(request.transport_time_seconds)  # Validación en el VO
            new_value = str(new_time.value)
            
            if old_value != new_value:
                cage.transport_time = new_time
                changes.append(ConfigChangeLogEntry.create(
                    cage_id=cage.id,
                    field_name="transport_time_seconds",
                    old_value=old_value,
                    new_value=new_value,
                    change_reason=request.change_reason
                ))
        
        # Solo persistir si hay cambios
        if changes:
            await self._cage_repo.save(cage)
            await self._config_log_repo.save_batch(changes)
