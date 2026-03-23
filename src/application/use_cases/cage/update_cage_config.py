"""Use case para actualizar la configuración de una jaula."""

from typing import List

from application.dtos.cage_dtos import (
    CageConfigResponse,
    CageResponse,
    UpdateCageConfigRequest,
)
from domain.aggregates.cage import Cage
from domain.enums import ActivityLogCategory, ActivityLogEventType
from domain.repositories import ICageActivityLogRepository, ICageFeedingRepository, ICageRepository
from domain.value_objects.activity_log_entry import ActivityLogEntry
from domain.value_objects.cage_configuration import CageConfiguration
from domain.value_objects.identifiers import CageId


class UpdateCageConfigUseCase:
    """Caso de uso para actualizar la configuración de una jaula."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        cage_feeding_repository: ICageFeedingRepository,
        activity_log_repository: ICageActivityLogRepository,
    ):
        self.cage_repository = cage_repository
        self.cage_feeding_repository = cage_feeding_repository
        self.activity_log_repository = activity_log_repository

    async def execute(self, cage_id: str, request: UpdateCageConfigRequest) -> CageResponse:
        """
        Actualiza la configuración de una jaula.

        Solo actualiza los campos proporcionados, manteniendo los demás.

        Args:
            cage_id: ID de la jaula
            request: Configuración a actualizar

        Returns:
            CageResponse con los datos actualizados

        Raises:
            ValueError: Si la jaula no existe
        """
        cage_id_vo = CageId.from_string(cage_id)
        cage = await self.cage_repository.find_by_id(cage_id_vo)
        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Construir nueva configuración preservando valores existentes
        current_config = cage.config

        new_config = CageConfiguration(
            fcr=request.fcr if request.fcr is not None else current_config.fcr,
            volume_m3=request.volume_m3 if request.volume_m3 is not None else current_config.volume_m3,
            max_density_kg_m3=request.max_density_kg_m3
            if request.max_density_kg_m3 is not None
            else current_config.max_density_kg_m3,
            transport_time_seconds=request.transport_time_seconds
            if request.transport_time_seconds is not None
            else current_config.transport_time_seconds,
            blower_power=request.blower_power if request.blower_power is not None else current_config.blower_power,
            daily_feeding_target_kg=request.daily_feeding_target_kg
            if request.daily_feeding_target_kg is not None
            else current_config.daily_feeding_target_kg,
        )

        # Detectar campos modificados antes de actualizar
        changed_fields = self._detect_changes(current_config, new_config, request)

        # Actualizar configuración
        cage.update_config(new_config)

        # Persistir cambios
        await self.cage_repository.save(cage)

        # Persistir logs de actividad por cada campo modificado
        for log_entry in changed_fields:
            await self.activity_log_repository.save(
                ActivityLogEntry.create(
                    cage_id=cage.id,
                    event_type=ActivityLogEventType.CONFIG,
                    category=ActivityLogCategory.CONFIG,
                    message=f"Configuración actualizada: {log_entry['field']}",
                    details=f"{log_entry['old']} → {log_entry['new']}",
                )
            )

        today_feeding_kg = await self.cage_feeding_repository.get_today_dispensed_by_cage(cage_id)

        return self._to_response(cage, today_feeding_kg)

    def _detect_changes(
        self,
        current_config: CageConfiguration,
        new_config: CageConfiguration,
        request: UpdateCageConfigRequest,
    ) -> List[dict]:
        """Detecta qué campos de configuración cambiaron."""
        changes = []
        field_map = [
            ("fcr", current_config.fcr, new_config.fcr),
            ("volume_m3", current_config.volume_m3, new_config.volume_m3),
            ("max_density_kg_m3", current_config.max_density_kg_m3, new_config.max_density_kg_m3),
            ("transport_time_seconds", current_config.transport_time_seconds, new_config.transport_time_seconds),
            ("blower_power", current_config.blower_power, new_config.blower_power),
            ("daily_feeding_target_kg", current_config.daily_feeding_target_kg, new_config.daily_feeding_target_kg),
        ]
        for field, old_val, new_val in field_map:
            if old_val != new_val:
                changes.append({
                    "field": field,
                    "old": str(old_val) if old_val is not None else "—",
                    "new": str(new_val) if new_val is not None else "—",
                })
        return changes

    def _to_response(self, cage: Cage, today_feeding_kg: float = 0.0) -> CageResponse:
        """Convierte la entidad a response DTO."""
        return CageResponse(
            id=str(cage.id.value),
            name=str(cage.name),
            status=cage.status.value,
            created_at=cage.created_at,
            fish_count=cage.fish_count,
            avg_weight_grams=cage.avg_weight_grams,
            biomass_kg=cage.biomass_kg,
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
