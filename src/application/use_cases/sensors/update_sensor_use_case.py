"""
Use case para actualizar la configuración de un sensor.

Permite modificar nombre, estado habilitado y umbrales de un sensor
específico de una línea de alimentación.
"""

from application.dtos.sensor_dtos import SensorDetailDTO, UpdateSensorDTO
from domain.exceptions import FeedingLineNotFoundException
from domain.repositories import IFeedingLineRepository
from domain.value_objects import SensorId, SensorName
from domain.value_objects.identifiers import LineId


class SensorNotFoundException(Exception):
    """Excepción cuando no se encuentra un sensor."""

    pass


class UpdateSensorUseCase:
    """
    Caso de uso: Actualizar configuración de un sensor.

    Responsabilidades:
    - Validar que la línea existe
    - Validar que el sensor existe en la línea
    - Aplicar las actualizaciones al sensor
    - Persistir los cambios
    """

    def __init__(self, feeding_line_repo: IFeedingLineRepository):
        self._feeding_line_repo = feeding_line_repo

    async def execute(
        self, line_id_str: str, sensor_id_str: str, update_dto: UpdateSensorDTO
    ) -> SensorDetailDTO:
        """
        Actualiza la configuración de un sensor.

        Args:
            line_id_str: ID de la línea
            sensor_id_str: ID del sensor
            update_dto: Datos a actualizar

        Returns:
            SensorDetailDTO: Sensor actualizado

        Raises:
            FeedingLineNotFoundException: Si la línea no existe
            SensorNotFoundException: Si el sensor no existe en la línea
        """
        line_id = LineId.from_string(line_id_str)
        sensor_id = SensorId.from_string(sensor_id_str)

        # 1. Obtener la línea
        line = await self._feeding_line_repo.find_by_id(line_id)
        if not line:
            raise FeedingLineNotFoundException(
                f"No se encontró la línea de alimentación con ID: {line_id}"
            )

        # 2. Buscar el sensor
        sensor = line.get_sensor_by_id(sensor_id)
        if not sensor:
            raise SensorNotFoundException(
                f"No se encontró el sensor con ID: {sensor_id} en la línea {line_id}"
            )

        # 3. Aplicar actualizaciones
        sensor.update(
            name=SensorName(update_dto.name) if update_dto.name else None,
            is_enabled=update_dto.is_enabled,
            warning_threshold=update_dto.warning_threshold,
            critical_threshold=update_dto.critical_threshold,
            clear_warning_threshold=update_dto.clear_warning_threshold,
            clear_critical_threshold=update_dto.clear_critical_threshold,
        )

        # 4. Persistir cambios
        await self._feeding_line_repo.save(line)

        # 5. Retornar sensor actualizado
        return SensorDetailDTO(
            id=str(sensor.id),
            name=str(sensor.name),
            sensor_type=sensor.sensor_type.value,
            is_enabled=sensor.is_enabled,
            warning_threshold=sensor.warning_threshold,
            critical_threshold=sensor.critical_threshold,
        )
