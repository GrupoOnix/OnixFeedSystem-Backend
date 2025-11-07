from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List

from .value_objects import (
    BlowDurationInSeconds, BlowerId, BlowerName, BlowerPowerPercentage, DoserId, 
    DoserName, DosingRange, DosingRate, SelectorCapacity, SelectorId, SelectorName, 
    SelectorSpeedProfile, SensorId, SensorName, SiloId
)


class IBlower(ABC):

    @property
    @abstractmethod
    def id(self) -> BlowerId: ...

    @property
    @abstractmethod
    def name(self) -> BlowerName: ...

    @name.setter
    @abstractmethod
    def name(self, name: BlowerName) -> None: ...

    @property
    @abstractmethod
    def non_feeding_power(self) -> BlowerPowerPercentage: ...

    @non_feeding_power.setter
    @abstractmethod
    def non_feeding_power(self, power: BlowerPowerPercentage) -> None: ...

    @property
    @abstractmethod
    def blow_before_feeding_time(self) -> BlowDurationInSeconds: ...

    @blow_before_feeding_time.setter
    @abstractmethod
    def blow_before_feeding_time(self, time: BlowDurationInSeconds) -> None: ...
    
    @property
    @abstractmethod
    def blow_after_feeding_time(self) -> BlowDurationInSeconds: ...

    @blow_after_feeding_time.setter
    @abstractmethod
    def blow_after_feeding_time(self, time: BlowDurationInSeconds) -> None: ...

    @property
    @abstractmethod
    def created_at(self) -> datetime: ...

    # -----------------
    # Métodos de Comportamiento (Reglas de Negocio)
    # -----------------
  
    @abstractmethod
    def validate_power_is_safe(self, power_to_check: BlowerPowerPercentage) -> bool:
        ...

class IDoser(ABC):

    @property
    @abstractmethod
    def id(self) -> DoserId: ...

    @property
    @abstractmethod
    def name(self) -> DoserName: ...

    @name.setter
    @abstractmethod
    def name(self, name: DoserName) -> None: ...
        
    @property
    @abstractmethod
    def assigned_silo_id(self) -> SiloId: ...

    @assigned_silo_id.setter
    @abstractmethod
    def assigned_silo_id(self, new_silo_id: SiloId) -> None: ...
        
    @property
    @abstractmethod
    def doser_type(self) -> str: ...
        
    @property
    @abstractmethod
    def dosing_range(self) -> DosingRange: ...

    @dosing_range.setter
    @abstractmethod
    def dosing_range(self, new_range: DosingRange) -> None: ...
        
    @property
    @abstractmethod
    def current_rate(self) -> DosingRate: ...

    @current_rate.setter
    @abstractmethod
    def current_rate(self, new_rate: DosingRate) -> None: ...

    # -----------------
    # Métodos de Comportamiento (Reglas de Negocio)
    # -----------------

    @abstractmethod
    def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        """
        Lógica de Negocio: Calibra el dosificador.
        Cada implementación (VariDoser, PulseDoser) lo hará
        de forma diferente, actualizando sus factores internos.
        """
        ...

    @abstractmethod
    def get_calibration_data(self) -> Dict[str, Any]:
        """Devuelve los datos de calibración actuales de la entidad."""
        ...

class ISelector(ABC):

    @property
    @abstractmethod
    def id(self) -> SelectorId: ...

    @property
    @abstractmethod
    def name(self) -> SelectorName: ...

    @name.setter
    @abstractmethod
    def name(self, name: SelectorName) -> None: ...
        
    @property
    @abstractmethod
    def capacity(self) -> SelectorCapacity: ...

    @property
    @abstractmethod
    def speed_profile(self) -> SelectorSpeedProfile: ...

    @speed_profile.setter
    @abstractmethod
    def speed_profile(self, new_profile: SelectorSpeedProfile) -> None: ...
        
    @property
    @abstractmethod
    def created_at(self) -> datetime: ...

    # -----------------
    # Métodos de Comportamiento (Reglas de Negocio)
    # -----------------

    @abstractmethod
    def validate_slot(self, slot_number: int) -> bool: ...

 
class ISensor(ABC):
    """
    Interfaz de dominio para un sensor
    """

    @property
    @abstractmethod
    def id(self) -> SensorId: ...

    @property
    @abstractmethod
    def name(self) -> SensorName: ...

    @property
    @abstractmethod
    def sensor_type(self) -> str: ...


    