from typing import Any, Dict

from domain.interfaces import IDoser
from domain.enums import DoserType
from domain.value_objects import (
    DoserId, DoserName, SiloId, DosingRange, DosingRate
)


class Doser(IDoser):

    def __init__(self,
                 name: DoserName,
                 assigned_silo_id: SiloId,
                 doser_type: DoserType,
                 dosing_range: DosingRange,
                 current_rate: DosingRate,
                 is_on: bool = True,
                 speed_percentage: int = 50,
                 *,
                 _skip_validation: bool = False):
        """
        Inicializa un Doser.
        
        Args:
            name: Nombre del doser
            assigned_silo_id: ID del silo asignado
            doser_type: Tipo de doser
            dosing_range: Rango de dosificación permitido
            current_rate: Tasa de dosificación configurada
            is_on: Estado encendido/apagado del doser
            _skip_validation: (Interno) Si True, omite validación de rango.
                              Solo usar para reconstrucción desde persistencia.
        """
        # Validar que current_rate esté dentro del rango permitido
        # Skip validation permite cargar dosers con rate=0 desde la DB
        if not _skip_validation and not dosing_range.contains(current_rate):
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
        self._is_on = is_on
        self._speed_percentage = speed_percentage
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
    def doser_type(self) -> DoserType:
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

    @property
    def speed_percentage(self) -> int:
        """Porcentaje de velocidad del motor (1-100)."""
        return self._speed_percentage

    @speed_percentage.setter
    def speed_percentage(self, value: int) -> None:
        if not (1 <= value <= 100):
            raise ValueError(f"speed_percentage debe estar entre 1 y 100, recibido: {value}")
        self._speed_percentage = value

    @property
    def is_on(self) -> bool:
        """Indica si el doser está encendido."""
        return self._is_on

    def turn_on(self) -> None:
        """
        Enciende el doser.
        
        Valida que el current_rate configurado esté dentro del rango permitido.
        Si no hay un rate válido configurado, la operación falla.
        
        Raises:
            ValueError: Si current_rate no está dentro del dosing_range
        """
        if not self._dosing_range.contains(self._current_rate):
            raise ValueError(
                f"No se puede encender el doser: la tasa configurada ({self._current_rate}) "
                f"está fuera del rango permitido ({self._dosing_range}). "
                f"Configure una tasa válida antes de encender."
            )
        self._is_on = True

    def stop(self) -> None:
        """
        Apaga el doser.
        
        El current_rate configurado se mantiene guardado para cuando
        se vuelva a encender.
        """
        self._is_on = False

    def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        print("Calibrando dosificador con datos:", calibration_data)
        return True

    def get_calibration_data(self) -> Dict[str, Any]:
        return self._calibration_data.copy()
