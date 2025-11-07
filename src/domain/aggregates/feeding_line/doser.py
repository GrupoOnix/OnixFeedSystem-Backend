from typing import Any, Dict

from domain.interfaces import IDoser
from domain.value_objects import (
    DoserId, DoserName, SiloId, DosingRange, DosingRate
)

class Doser(IDoser):
    
    def __init__(self,
                 name: DoserName,
                 assigned_silo_id: SiloId,
                 doser_type: str,
                 dosing_range: DosingRange,
                 current_rate: DosingRate):
        
        if not dosing_range.contains(current_rate):
            raise ValueError(
                f"La tasa de dosificación inicial ({current_rate}) "
                f"está fuera del rango permitido ({dosing_range})."
            )

        self._id = DoserId.generate()
        self._name = name
        self._assigned_silo_id = assigned_silo_id
        self._doser_type = doser_type
        self._dosing_range = dosing_range
        self._current_rate = current_rate
        self._calibration_data: Dict[str, Any] = {"status": "uncalibrated"}


    @property
    def id(self) -> DoserId:
        return self._id

    @property
    def name(self) -> DoserName:
        return self._name
    
    @name.setter
    def name(self, name: DoserName) -> None:
        self._name = name
        
    @property
    def assigned_silo_id(self) -> SiloId:
        return self._assigned_silo_id
    
    @assigned_silo_id.setter
    def assigned_silo_id(self, new_silo_id: SiloId) -> None:
        self._assigned_silo_id = new_silo_id
        
    @property
    def doser_type(self) -> str:
        return self._doser_type
        
    @property
    def dosing_range(self) -> DosingRange:
        return self._dosing_range
    
    @dosing_range.setter
    def dosing_range(self, new_range: DosingRange) -> None:
        #TODO Cuando exista calibración comprobar que el nuevo rango
        #TODO incluye la tasa actual
        self._dosing_range = new_range
        
    @property
    def current_rate(self) -> DosingRate:
        return self._current_rate
    
    @current_rate.setter
    def current_rate(self, new_rate: DosingRate) -> None:
        if not self._dosing_range.contains(new_rate):
            raise ValueError(f"La tasa {new_rate} está fuera del rango {self._dosing_range}")
            
        self._current_rate = new_rate


    def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        print("Calibrando dosificador con datos:", calibration_data)
        return True

    def get_calibration_data(self) -> Dict[str, Any]:
        return self._calibration_data.copy()