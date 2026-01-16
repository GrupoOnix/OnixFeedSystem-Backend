"""Caso de uso para actualizar la configuración de un blower."""

from application.dtos.feeding_line_dtos import UpdateBlowerRequest
from domain.exceptions import FeedingLineNotFoundException
from domain.repositories import IFeedingLineRepository
from domain.value_objects import (
    BlowDurationInSeconds,
    BlowerName,
    BlowerPowerPercentage,
    LineId,
)


class UpdateBlowerUseCase:
    """Caso de uso para actualizar la configuración de un blower."""

    def __init__(self, feeding_line_repository: IFeedingLineRepository):
        self._feeding_line_repository = feeding_line_repository

    async def execute(self, line_id: str, request: UpdateBlowerRequest) -> None:
        """
        Actualiza la configuración de un blower.

        Args:
            line_id: ID de la línea de alimentación
            request: Datos de actualización del blower

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
            feeding_line.blower.name = BlowerName(request.name)

        # Actualizar potencia sin alimentación si se proporciona
        if request.non_feeding_power is not None:
            feeding_line.blower.non_feeding_power = BlowerPowerPercentage(
                request.non_feeding_power
            )

        # Actualizar potencia actual si se proporciona
        if request.current_power is not None:
            feeding_line.blower.current_power = BlowerPowerPercentage(
                request.current_power
            )

        # Actualizar tiempo de soplado antes si se proporciona
        if request.blow_before_feeding_time is not None:
            feeding_line.blower.blow_before_feeding_time = BlowDurationInSeconds(
                request.blow_before_feeding_time
            )

        # Actualizar tiempo de soplado después si se proporciona
        if request.blow_after_feeding_time is not None:
            feeding_line.blower.blow_after_feeding_time = BlowDurationInSeconds(
                request.blow_after_feeding_time
            )

        # Persistir cambios
        await self._feeding_line_repository.save(feeding_line)
