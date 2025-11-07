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
    CageNotFoundException
)

class FeedingLine:
    """
    Agregado Raíz (AR) para una Línea de Alimentación.
    
    RESPONSABILIDAD: Proteger las invariantes y reglas de negocio
    relacionadas con la CONFIGURACIÓN y COMPOSICIÓN de la línea.
    
    """

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
        
        # Regla 1: Validar composición mínima
        if not blower:
            raise InsufficientComponentsException("Se requiere un Blower.")
        if not dosers or len(dosers) == 0:
            raise InsufficientComponentsException("Se requiere al menos un Doser.")
        if not selector:
            raise InsufficientComponentsException("Se requiere un Selector.")

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
    
