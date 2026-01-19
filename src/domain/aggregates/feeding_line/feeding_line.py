from datetime import datetime
from typing import Any, List, Optional, Tuple, cast

from ...exceptions import DuplicateSensorTypeException, InsufficientComponentsException
from ...interfaces import IBlower, ICooler, IDoser, ISelector, ISensor
from ...value_objects import LineId, LineName, SensorId


class FeedingLine:
    def __init__(self, name: LineName):
        self._id = LineId.generate()
        self._name = name
        self._blower: Optional[IBlower] = None
        self._dosers: Tuple[IDoser, ...] = ()
        self._selector: Optional[ISelector] = None
        self._sensors: Tuple[ISensor, ...] = ()
        self._cooler: Optional[ICooler] = None
        self._created_at = datetime.utcnow()

    @classmethod
    def create(
        cls,
        name: LineName,
        blower: IBlower,
        dosers: List[IDoser],
        selector: ISelector,
        sensors: List[ISensor] = [],
        cooler: Optional[ICooler] = None,
    ) -> "FeedingLine":
        # Regla FA1: Validar composición mínima
        if not blower:
            raise InsufficientComponentsException("Se requiere un Blower.")
        if not dosers or len(dosers) == 0:
            raise InsufficientComponentsException("Se requiere al menos un Doser.")
        if not selector:
            raise InsufficientComponentsException("Se requiere un Selector.")
        # NOTA: Cooler es OPCIONAL, no se valida aquí

        # Regla FA7: Validar sensores únicos por tipo
        cls._validate_unique_sensor_types(sensors or [])

        # Creamos la instancia
        line = cls(name)

        # Asignamos los componentes
        line._blower = blower
        line._dosers = tuple(dosers)
        line._selector = selector
        line._sensors = tuple(sensors or [])
        line._cooler = cooler

        return line

    @property
    def id(self) -> LineId:
        return self._id

    @property
    def name(self) -> LineName:
        return self._name

    @name.setter
    def name(self, name: LineName) -> None:
        self._name = name

    @property
    def blower(self) -> IBlower:
        return cast(IBlower, self._blower)

    @property
    def dosers(self) -> Tuple[IDoser, ...]:
        return self._dosers

    @property
    def selector(self) -> ISelector:
        return cast(ISelector, self._selector)

    @property
    def cooler(self) -> Optional[ICooler]:
        """
        Cooler opcional de la línea.

        El cooler enfría el aire entre el blower y el doser.
        No todas las líneas lo tienen instalado.
        """
        return self._cooler

    def get_doser_by_id(self, doser_id: Any) -> Optional[IDoser]:
        for doser in self._dosers:
            if doser.id == doser_id:
                return doser
        return None

    def get_sensor_by_id(self, sensor_id: SensorId) -> Optional[ISensor]:
        """
        Busca un sensor por su ID.

        Args:
            sensor_id: ID del sensor a buscar

        Returns:
            El sensor si existe, None si no se encuentra
        """
        for sensor in self._sensors:
            if sensor.id == sensor_id:
                return sensor
        return None

    def update_components(
        self,
        blower: IBlower,
        dosers: List[IDoser],
        selector: ISelector,
        sensors: Optional[List[ISensor]] = None,
        cooler: Optional[ICooler] = None,
    ) -> None:
        # Reutilizar validación FA1: Composición mínima
        if not blower:
            raise InsufficientComponentsException("Se requiere un Blower.")
        if not dosers or len(dosers) == 0:
            raise InsufficientComponentsException("Se requiere al menos un Doser.")
        if not selector:
            raise InsufficientComponentsException("Se requiere un Selector.")

        # Reutilizar validación FA7: Sensores únicos por tipo
        self._validate_unique_sensor_types(sensors or [])

        # Asignar los nuevos componentes (sobrescribiendo los antiguos)
        self._blower = blower
        self._dosers = tuple(dosers)
        self._selector = selector
        self._sensors = tuple(sensors or [])
        self._cooler = cooler

    @staticmethod
    def _validate_unique_sensor_types(sensors: List[ISensor]) -> None:
        sensor_types_seen = set()

        for sensor in sensors:
            if sensor.sensor_type in sensor_types_seen:
                raise DuplicateSensorTypeException(
                    f"Ya existe un sensor de tipo '{sensor.sensor_type.value}' en la línea. "
                    f"Solo puede haber un sensor de cada tipo."
                )
            sensor_types_seen.add(sensor.sensor_type)
