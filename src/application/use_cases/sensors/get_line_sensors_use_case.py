"""
Use case para obtener los sensores configurados de una línea.

Este use case retorna la lista de sensores de una línea con su configuración
actual (nombre, tipo, estado habilitado, umbrales).
"""

from application.dtos.sensor_dtos import SensorDetailDTO, SensorsListDTO
from domain.exceptions import FeedingLineNotFoundException
from domain.repositories import IFeedingLineRepository
from domain.value_objects.identifiers import LineId


class GetLineSensorsUseCase:
    """
    Caso de uso: Obtener lista de sensores de una línea.

    Responsabilidades:
    - Validar que la línea existe
    - Retornar lista de sensores con su configuración
    """

    def __init__(self, feeding_line_repo: IFeedingLineRepository):
        self._feeding_line_repo = feeding_line_repo

    async def execute(self, line_id_str: str) -> SensorsListDTO:
        """
        Obtiene los sensores configurados de una línea.

        Args:
            line_id_str: ID de la línea en formato string

        Returns:
            SensorsListDTO: Lista de sensores con su configuración

        Raises:
            FeedingLineNotFoundException: Si la línea no existe
        """
        line_id = LineId.from_string(line_id_str)

        line = await self._feeding_line_repo.find_by_id(line_id)
        if not line:
            raise FeedingLineNotFoundException(
                f"No se encontró la línea de alimentación con ID: {line_id}"
            )

        sensors_dto = [
            SensorDetailDTO(
                id=str(sensor.id),
                name=str(sensor.name),
                sensor_type=sensor.sensor_type.value,
                is_enabled=sensor.is_enabled,
                warning_threshold=sensor.warning_threshold,
                critical_threshold=sensor.critical_threshold,
            )
            for sensor in line.sensors
        ]

        return SensorsListDTO(line_id=str(line_id), sensors=sensors_dto)
