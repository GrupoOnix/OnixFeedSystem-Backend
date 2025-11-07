from datetime import datetime
from domain.enums import CageStatus
from domain.exceptions import CageNotAvailableException
from domain.value_objects import CageId, CageName

#TODO: Falta agregar atributos de cantidad de peces y peso promedio y sus validaciones

class Cage:
    def __init__(self, name: CageName, status: CageStatus = CageStatus.AVAILABLE):
        self._id = CageId.generate()
        self._name = name
        # self._fish_count = fish_count
        # self._average_weight_g = average_weight_g
        self._status = status
        self._created_at = datetime.utcnow()

    @property
    def id(self) -> CageId:
        return self._id
    
    @property
    def name(self) -> CageName:
        return self._name

    @name.setter
    def name(self, new_name: CageName) -> None:
        self._name = new_name

    @property
    def status(self) -> CageStatus:
        return self._status
    
    @status.setter
    def status(self, new_status: CageStatus) -> None:
        self._status = new_status

# --------------------- METODOS -----------------------------------------------

    def assign_to_line(self) -> None:

        if self._status != CageStatus.AVAILABLE:
            raise CageNotAvailableException(
                f"La jaula '{self.name}' no está disponible (estado actual: {self.status.value})."
            )
        
        print(f"Jaula '{self.name}': Estado cambiado a {CageStatus.IN_USE.value}.")
        self._status = CageStatus.IN_USE

    def release_from_line(self) -> None:

        if self._status != CageStatus.IN_USE:
            print(f"Advertencia: La jaula '{self.name}' ya estaba liberada.")
        
        print(f"Jaula '{self.name}': Estado cambiado a {CageStatus.AVAILABLE.value}.")
        self._status = CageStatus.AVAILABLE
        