"""
Use case para obtener las lecturas en tiempo real de los sensores de una línea.

Este use case coordina la lectura de sensores desde el PLC/simulador,
validando que la línea exista antes de solicitar las lecturas.
Aplica umbrales personalizados y filtra sensores deshabilitados.
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from domain.aggregates.system_config import SystemConfig
from domain.dtos.machine_io_v2 import SensorReading, SensorReadings
from domain.enums import SensorType
from domain.exceptions import FeedingLineNotFoundException
from domain.interfaces import IFeedingMachine, ISensor
from domain.repositories import IFeedingLineRepository, ISystemConfigRepository
from domain.value_objects.identifiers import LineId

class GetSensorReadingsUseCase:
    """
    Caso de uso: Obtener lecturas de sensores de una línea de alimentación.

    Responsabilidades:
    - Validar que la línea existe en el sistema
    - Solicitar lecturas al PLC/simulador
    - Filtrar sensores deshabilitados
    - Aplicar umbrales personalizados si están configurados
    - Retornar datos estructurados de sensores
    """

    def __init__(
        self,
        feeding_line_repo: IFeedingLineRepository,
        feeding_machine: IFeedingMachine,
        system_config_repo: ISystemConfigRepository,
    ):
        self._feeding_line_repo = feeding_line_repo
        self._feeding_machine = feeding_machine
        self._system_config_repo = system_config_repo

    async def execute(self, line_id_str: str) -> SensorReadings:
        """
        Obtiene las lecturas actuales de todos los sensores habilitados de una línea.

        Args:
            line_id_str: ID de la línea en formato string

        Returns:
            SensorReadings: Lecturas de sensores habilitados con timestamp

        Raises:
            FeedingLineNotFoundException: Si la línea no existe
        """
        # 1. Validar que la línea existe
        line_id = LineId.from_string(line_id_str)

        line = await self._feeding_line_repo.find_by_id(line_id)
        if not line:
            raise FeedingLineNotFoundException(f"No se encontró la línea de alimentación con ID: {line_id}")

        # 2. Crear mapa de sensores por tipo para fácil acceso
        sensor_map: Dict[SensorType, ISensor] = {sensor.sensor_type: sensor for sensor in line.sensors}

        # 3. Obtener lecturas del PLC/simulador
        raw_readings = await self._feeding_machine.get_sensor_readings(line_id)
        system_config = await self._system_config_repo.get()

        # 4. Filtrar y aplicar umbrales personalizados
        filtered_readings = []
        for reading in raw_readings.readings:
            sensor = sensor_map.get(reading.sensor_type)

            # Filtrar sensores deshabilitados
            if sensor and not sensor.is_enabled:
                continue

            # Aplicar umbrales personalizados si existen
            is_warning, is_critical = self._apply_thresholds(
                reading.sensor_type,
                reading.value,
                sensor,
                system_config,
            )

            # Crear nueva lectura con umbrales aplicados
            filtered_readings.append(
                SensorReading(
                    sensor_id=reading.sensor_id,
                    sensor_type=reading.sensor_type,
                    value=reading.value,
                    unit=reading.unit,
                    timestamp=reading.timestamp,
                    is_warning=is_warning,
                    is_critical=is_critical,
                )
            )

        return SensorReadings(
            line_id=str(line_id),
            readings=filtered_readings,
            timestamp=datetime.now(timezone.utc),
        )

    def _apply_thresholds(
        self,
        sensor_type: SensorType,
        value: float,
        sensor: Optional[ISensor],
        system_config: SystemConfig,
    ) -> tuple[bool, bool]:
        """
        Aplica umbrales para determinar warning/critical.

        Usa umbrales personalizados del sensor si están configurados,
        de lo contrario usa los umbrales por defecto.

        Returns:
            Tupla (is_warning, is_critical)
        """
        # Los umbrales por sensor prevalecen; los globales se usan como respaldo.
        global_thresholds = {
            SensorType.TEMPERATURE: {
                "warning": system_config.temperature_warning_threshold,
                "critical": system_config.temperature_critical_threshold,
            },
            SensorType.PRESSURE: {
                "warning": system_config.pressure_warning_threshold,
                "critical": system_config.pressure_critical_threshold,
            },
            SensorType.FLOW: {
                "warning": system_config.flow_warning_threshold,
                "critical": system_config.flow_critical_threshold,
            },
        }.get(sensor_type, {})

        if sensor and sensor.warning_threshold is not None:
            warning_threshold = sensor.warning_threshold
        else:
            warning_threshold = global_thresholds.get("warning", float("inf"))

        if sensor and sensor.critical_threshold is not None:
            critical_threshold = sensor.critical_threshold
        else:
            critical_threshold = global_thresholds.get("critical", float("inf"))

        is_critical = value > critical_threshold
        is_warning = value > warning_threshold and not is_critical

        return is_warning, is_critical
