from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, cast
from ...interfaces import IBlower, IDoser, ISelector, ISensor
from ...value_objects import (
    LineId, LineName, CageId, SiloId
)
from ...exceptions import (
    InsufficientComponentsException,
    DuplicateSensorTypeException
)

class FeedingLine:

    def __init__(self, name: LineName):
        self._id = LineId.generate()
        self._name = name
        self._blower: Optional[IBlower] = None
        self._dosers: Tuple[IDoser, ...] = ()
        self._selector: Optional[ISelector] = None
        self._sensors: Tuple[ISensor, ...] = ()
        self._created_at = datetime.utcnow() #TODO: ver que hacer con esto

    @classmethod
    def create(cls,
               name: LineName,
               blower: IBlower,
               dosers: List[IDoser],
               selector: ISelector,
               sensors: List[ISensor] = []
               ) -> 'FeedingLine':
        
        # Regla FA1: Validar composición mínima
        if not blower:
            raise InsufficientComponentsException("Se requiere un Blower.")
        if not dosers or len(dosers) == 0:
            raise InsufficientComponentsException("Se requiere al menos un Doser.")
        if not selector:
            raise InsufficientComponentsException("Se requiere un Selector.")

        # Regla FA7: Validar sensores únicos por tipo
        cls._validate_unique_sensor_types(sensors or [])

        # Creamos la instancia
        line = cls(name)
        
        # Asignamos los componentes (los "cerebros")
        line._blower = blower
        line._dosers = tuple(dosers)
        line._selector = selector
        line._sensors = tuple(sensors or [])

        # Regla 2: Validar secuencia lineal (si es necesario)
        # line._validate_linear_sequence() # Si tuvieras esta lógica
        
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


    def get_doser_by_id(self, doser_id: Any) -> Optional[IDoser]:

        for doser in self._dosers:
            if doser.id == doser_id:
                return doser
        return None
    

    def update_components(self, 
                         blower: IBlower, 
                         dosers: List[IDoser], 
                         selector: ISelector, 
                         sensors: Optional[List[ISensor]] = None) -> None:

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
    
