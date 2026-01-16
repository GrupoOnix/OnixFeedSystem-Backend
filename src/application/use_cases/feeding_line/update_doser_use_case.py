"""Caso de uso para actualizar la configuración de un doser."""

from application.dtos.feeding_line_dtos import UpdateDoserRequest
from domain.exceptions import FeedingLineNotFoundException
from domain.repositories import IFeedingLineRepository
from domain.value_objects import (
    DoserId,
    DoserName,
    DosingRange,
    DosingRate,
    LineId,
    SiloId,
)


class UpdateDoserUseCase:
    """Caso de uso para actualizar la configuración de un doser."""

    def __init__(self, feeding_line_repository: IFeedingLineRepository):
        self._feeding_line_repository = feeding_line_repository

    async def execute(
        self, line_id: str, doser_id: str, request: UpdateDoserRequest
    ) -> None:
        """
        Actualiza la configuración de un doser específico.

        Args:
            line_id: ID de la línea de alimentación
            doser_id: ID del doser a actualizar
            request: Datos de actualización del doser

        Raises:
            FeedingLineNotFoundException: Si la línea no existe
            ValueError: Si el doser no existe o los valores son inválidos
        """
        # Obtener línea
        feeding_line = await self._feeding_line_repository.find_by_id(LineId(line_id))

        if not feeding_line:
            raise FeedingLineNotFoundException(
                f"Línea de alimentación con ID {line_id} no encontrada"
            )

        # Buscar el doser específico
        doser_id_obj = DoserId.from_string(doser_id)
        doser = feeding_line.get_doser_by_id(doser_id_obj)
        if not doser:
            raise ValueError(
                f"Doser con ID {doser_id} no encontrado en la línea {line_id}"
            )

        # Actualizar nombre si se proporciona
        if request.name is not None:
            doser.name = DoserName(request.name)

        # Actualizar silo asignado si se proporciona
        if request.assigned_silo_id is not None:
            doser.assigned_silo_id = SiloId(request.assigned_silo_id)

        # Actualizar rango de dosificación si se proporciona
        if request.dosing_range_min is not None or request.dosing_range_max is not None:
            # Obtener valores actuales
            current_min = doser.dosing_range.min_rate
            current_max = doser.dosing_range.max_rate
            current_unit = doser.dosing_range.unit

            # Usar nuevos valores o mantener los actuales
            new_min = (
                request.dosing_range_min
                if request.dosing_range_min is not None
                else current_min
            )
            new_max = (
                request.dosing_range_max
                if request.dosing_range_max is not None
                else current_max
            )

            # Crear nuevo rango
            new_range = DosingRange(
                min_rate=new_min, max_rate=new_max, unit=current_unit
            )

            # Actualizar el doser
            doser.dosing_range = new_range

        # Actualizar tasa actual si se proporciona
        if request.current_rate is not None:
            # La validación del rango se hace en el setter del doser
            doser.current_rate = DosingRate(
                value=request.current_rate, unit=doser.current_rate.unit
            )

        # Persistir cambios
        await self._feeding_line_repository.save(feeding_line)
