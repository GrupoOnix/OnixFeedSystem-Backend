from datetime import datetime, timezone
from typing import Optional

from ...enums import SensorType
from ...interfaces import ISensor
from ...value_objects import SensorId, SensorName


class Sensor(ISensor):
    """
    Entidad Sensor que representa un componente de medición en la línea de alimentación.

    Los sensores pueden ser de diferentes tipos (temperatura, presión, caudal).
    Regla de negocio: Una línea solo puede tener un sensor de cada tipo.

    Los sensores pueden ser habilitados/deshabilitados para mantenimiento,
    y tienen umbrales configurables para alertas de warning y critical.
    """

    def __init__(
        self,
        name: SensorName,
        sensor_type: SensorType,
        is_enabled: bool = True,
        warning_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
    ):
        """
        Crea una nueva instancia de Sensor.

        Args:
            name: Nombre del sensor
            sensor_type: Tipo de sensor (TEMPERATURE, PRESSURE, FLOW)
            is_enabled: Si el sensor está habilitado para lecturas
            warning_threshold: Umbral para advertencia (opcional)
            critical_threshold: Umbral para alerta crítica (opcional)
        """
        self._id = SensorId.generate()
        self._name = name
        self._sensor_type = sensor_type
        self._is_enabled = is_enabled
        self._warning_threshold = warning_threshold
        self._critical_threshold = critical_threshold
        self._created_at = datetime.now(timezone.utc)

    @property
    def id(self) -> SensorId:
        return self._id

    @property
    def name(self) -> SensorName:
        return self._name

    @name.setter
    def name(self, name: SensorName) -> None:
        self._name = name

    @property
    def sensor_type(self) -> SensorType:
        return self._sensor_type

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    @property
    def warning_threshold(self) -> Optional[float]:
        return self._warning_threshold

    @warning_threshold.setter
    def warning_threshold(self, value: Optional[float]) -> None:
        self._warning_threshold = value

    @property
    def critical_threshold(self) -> Optional[float]:
        return self._critical_threshold

    @critical_threshold.setter
    def critical_threshold(self, value: Optional[float]) -> None:
        self._critical_threshold = value

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def enable(self) -> None:
        """Habilita el sensor para lecturas."""
        self._is_enabled = True

    def disable(self) -> None:
        """Deshabilita el sensor (no se incluirá en lecturas)."""
        self._is_enabled = False

    def update(
        self,
        name: Optional[SensorName] = None,
        is_enabled: Optional[bool] = None,
        warning_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
        clear_warning_threshold: bool = False,
        clear_critical_threshold: bool = False,
    ) -> None:
        """
        Actualiza las propiedades configurables del sensor.

        Args:
            name: Nuevo nombre (opcional)
            is_enabled: Nuevo estado habilitado (opcional)
            warning_threshold: Nuevo umbral de warning (opcional)
            critical_threshold: Nuevo umbral crítico (opcional)
            clear_warning_threshold: Si True, limpia el umbral de warning
            clear_critical_threshold: Si True, limpia el umbral crítico
        """
        if name is not None:
            self._name = name

        if is_enabled is not None:
            self._is_enabled = is_enabled

        if clear_warning_threshold:
            self._warning_threshold = None
        elif warning_threshold is not None:
            self._warning_threshold = warning_threshold

        if clear_critical_threshold:
            self._critical_threshold = None
        elif critical_threshold is not None:
            self._critical_threshold = critical_threshold
