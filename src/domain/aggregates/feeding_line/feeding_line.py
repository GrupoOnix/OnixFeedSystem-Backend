from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, cast
from ...interfaces import IBlower, IDoser, ISelector, ISensor
from ...value_objects import (
    LineId, LineName, SlotAssignment, CageId, SiloId, SlotNumber
)
from ...exceptions import (
    InsufficientComponentsException,
    DuplicateSlotAssignmentException,
    InvalidSlotAssignmentException,
    SlotNotFoundException,
    CageNotFoundException,
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
        self._slot_assignments: Dict[int, SlotAssignment] = {} # Dict para búsquedas rápidas
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
    

    def get_slot_assignments(self) -> List[SlotAssignment]:
        return list(self._slot_assignments.values())
    

    def assign_cage_to_slot(self, slot_number: int, cage_id: CageId) -> None:

        assert self._selector is not None, "Selector no fue inicializado correctamente."
        
        # Regla 1: El slot debe ser válido para el selector de esta línea
        if not self._selector.validate_slot(slot_number):
            raise InvalidSlotAssignmentException(
                f"Slot {slot_number} no es válido para el selector '{self._selector.name}'."
            )

        # Regla 2: El slot no puede estar ya asignado
        if slot_number in self._slot_assignments:
            raise DuplicateSlotAssignmentException(
                f"Slot {slot_number} ya está asignado a la jaula {self._slot_assignments[slot_number].cage_id}."
            )
            
        # Regla 3: La jaula no puede estar asignada a otro slot EN ESTA LÍNEA
        for assignment in self._slot_assignments.values():
            if assignment.cage_id == cage_id:
                raise DuplicateSlotAssignmentException(
                    f"Jaula {cage_id} ya está asignada al slot {assignment.slot_number}."
                )

        slot_vo = SlotNumber(slot_number)
        assignment = SlotAssignment(slot_vo, cage_id)
        self._slot_assignments[slot_number] = assignment
        
        # Emitir un Evento de Dominio
        # self.register_event(SlotAssigned(line_id=self.id, ...))


    def remove_assignment_from_slot(self, slot_number: int) -> None:

        if slot_number not in self._slot_assignments:
            raise SlotNotFoundException(f"Slot {slot_number} no tiene asignación.")
            
        del self._slot_assignments[slot_number]


    def get_cage_for_slot(self, slot_number: int) -> CageId:

        if slot_number not in self._slot_assignments:
            raise SlotNotFoundException(f"Slot {slot_number} no está asignado.")
        return self._slot_assignments[slot_number].cage_id
    

    def get_slot_for_cage(self, cage_id: CageId) -> SlotNumber:
  
        for assignment in self._slot_assignments.values():
            if assignment.cage_id == cage_id:
                return assignment.slot_number
        raise CageNotFoundException(f"Jaula {cage_id} no está asignada en esta línea.")
    

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


    def update_assignments(self, new_assignments: List[SlotAssignment]) -> None:
        """
        Actualiza las asignaciones de jaulas a slots de la línea.
        
        Este método solo valida reglas internas (FA4). La validación de reglas 
        externas (FA3 - "Jaula ya en uso por OTRA línea") es responsabilidad 
        del Caso de Uso.
        
        Args:
            new_assignments: Lista de nuevas asignaciones slot-jaula
            
        Raises:
            DuplicateSlotAssignmentException: Si hay slots o jaulas duplicadas
            InvalidSlotAssignmentException: Si un slot no es válido para el selector
        """
        assert self._selector is not None, "Selector no fue inicializado correctamente."
        
        # Limpiar el estado actual
        self._slot_assignments.clear()
        
        # Validar duplicados (FA4) usando sets temporales
        seen_slots = set()
        seen_cages = set()
        
        for assignment in new_assignments:
            slot_value = assignment.slot_number.value
            cage_id = assignment.cage_id
            
            # Verificar duplicado de slot
            if slot_value in seen_slots:
                raise DuplicateSlotAssignmentException(
                    f"Slot {slot_value} aparece duplicado en la lista de asignaciones."
                )
            
            # Verificar duplicado de jaula
            if cage_id in seen_cages:
                raise DuplicateSlotAssignmentException(
                    f"Jaula {cage_id} aparece duplicada en la lista de asignaciones."
                )
            
            seen_slots.add(slot_value)
            seen_cages.add(cage_id)
        
        # Iterar y re-validar cada asignación
        for assignment in new_assignments:
            slot_value = assignment.slot_number.value
            
            # Reutilizar validación del selector
            if not self._selector.validate_slot(slot_value):
                raise InvalidSlotAssignmentException(
                    f"Slot {slot_value} no es válido para el selector '{self._selector.name}'."
                )
            
            # Añadir la asignación al diccionario (ahora vacío)
            self._slot_assignments[slot_value] = assignment
    
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
    
