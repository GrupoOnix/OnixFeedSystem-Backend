"""
Use case para obtener las lecturas en tiempo real de los sensores de una línea.

Este use case coordina la lectura de sensores desde el PLC/simulador,
validando que la línea exista antes de solicitar las lecturas.
"""

from domain.dtos.machine_io_v2 import SensorReadings
from domain.exceptions import FeedingLineNotFoundException
from domain.interfaces import IFeedingMachine
from domain.repositories import IFeedingLineRepository
from domain.value_objects.identifiers import LineId


class GetSensorReadingsUseCase:
    """
    Caso de uso: Obtener lecturas de sensores de una línea de alimentación.

    Responsabilidades:
    - Validar que la línea existe en el sistema
    - Solicitar lecturas al PLC/simulador
    - Retornar datos estructurados de sensores
    """

    def __init__(
        self,
        feeding_line_repo: IFeedingLineRepository,
        feeding_machine: IFeedingMachine,
    ):
        self._feeding_line_repo = feeding_line_repo
        self._feeding_machine = feeding_machine

    async def execute(self, line_id_str: str) -> SensorReadings:
        """
        Obtiene las lecturas actuales de todos los sensores de una línea.

        Args:
            line_id_str: ID de la línea en formato string

        Returns:
            SensorReadings: Lecturas de todos los sensores con timestamp

        Raises:
            FeedingLineNotFoundException: Si la línea no existe
        """
        # 1. Validar que la línea existe
        line_id = LineId.from_string(line_id_str)

        line = await self._feeding_line_repo.find_by_id(line_id)
        if not line:
            raise FeedingLineNotFoundException(
                f"No se encontró la línea de alimentación con ID: {line_id}"
            )

        # 2. Obtener lecturas del PLC/simulador
        sensor_readings = await self._feeding_machine.get_sensor_readings(line_id)

        return sensor_readings
