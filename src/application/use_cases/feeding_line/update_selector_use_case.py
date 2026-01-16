"""Caso de uso para actualizar la configuración de un selector."""

from application.dtos.feeding_line_dtos import UpdateSelectorRequest
from domain.exceptions import FeedingLineNotFoundException
from domain.repositories import IFeedingLineRepository
from domain.value_objects import (
    BlowerPowerPercentage,
    LineId,
    SelectorName,
    SelectorSpeedProfile,
)


class UpdateSelectorUseCase:
    """Caso de uso para actualizar la configuración de un selector."""

    def __init__(self, feeding_line_repository: IFeedingLineRepository):
        self._feeding_line_repository = feeding_line_repository

    async def execute(self, line_id: str, request: UpdateSelectorRequest) -> None:
        """
        Actualiza la configuración de un selector.

        Args:
            line_id: ID de la línea de alimentación
            request: Datos de actualización del selector

        Raises:
            FeedingLineNotFoundException: Si la línea no existe
            ValueError: Si los valores son inválidos
        """
        # Obtener línea
        feeding_line = await self._feeding_line_repository.find_by_id(LineId(line_id))

        if not feeding_line:
            raise FeedingLineNotFoundException(
                f"Línea de alimentación con ID {line_id} no encontrada"
            )

        # Actualizar nombre si se proporciona
        if request.name is not None:
            feeding_line.selector.name = SelectorName(request.name)

        # Actualizar perfil de velocidad si se proporciona
        if request.fast_speed is not None or request.slow_speed is not None:
            # Obtener valores actuales
            current_fast = feeding_line.selector.speed_profile.fast_speed.value
            current_slow = feeding_line.selector.speed_profile.slow_speed.value

            # Usar nuevos valores o mantener los actuales
            new_fast = (
                request.fast_speed if request.fast_speed is not None else current_fast
            )
            new_slow = (
                request.slow_speed if request.slow_speed is not None else current_slow
            )

            # Crear nuevo perfil de velocidad
            new_profile = SelectorSpeedProfile(
                fast_speed=BlowerPowerPercentage(new_fast),
                slow_speed=BlowerPowerPercentage(new_slow),
            )

            # Actualizar el selector
            feeding_line.selector.speed_profile = new_profile

        # Actualizar current_slot si se proporciona
        if request.current_slot is not None:
            # La validación del slot se hace en el setter del selector
            feeding_line.selector.current_slot = request.current_slot

        # Persistir cambios
        await self._feeding_line_repository.save(feeding_line)
