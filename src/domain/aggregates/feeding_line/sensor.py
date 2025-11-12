from datetime import datetime

from ...interfaces import ISensor
from ...value_objects import SensorId, SensorName
from ...enums import SensorType


class Sensor(ISensor):
    """
    Entidad Sensor que representa un componente de medición en la línea de alimentación.
    
    Los sensores pueden ser de diferentes tipos (temperatura, presión, caudal).
    Regla de negocio: Una línea solo puede tener un sensor de cada tipo.
    """

    def __init__(self, name: SensorName, sensor_type: SensorType):
        """
        Crea una nueva instancia de Sensor.
        
        Args:
            name: Nombre del sensor
            sensor_type: Tipo de sensor (TEMPERATURE, PRESSURE, FLOW)
        """
        self._id = SensorId.generate()
        self._name = name
        self._sensor_type = sensor_type
        self._created_at = datetime.utcnow()

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
    def created_at(self) -> datetime:
        return self._created_at
