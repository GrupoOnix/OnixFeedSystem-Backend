from typing import Any, Dict, Iterable, Optional, Tuple

from domain.interfaces import IDoser
from domain.enums import DoserType
from domain.value_objects import DoserId, DoserName, SiloId, DosingRange, DosingRate


class Doser(IDoser):
    def __init__(
        self,
        name: DoserName,
        assigned_silo_ids: Iterable[SiloId],
        doser_type: DoserType,
        dosing_range: DosingRange,
        current_rate: DosingRate,
        is_on: bool = False,
        speed_percentage: int = 50,
        calibrated_grams_per_second: Optional[float] = None,
        pulse_on_time: Optional[float] = None,
        pulse_off_time: Optional[float] = None,
        pulse_speed: Optional[int] = None,
        *,
        _skip_validation: bool = False,
        _existing_id: str | None = None,
    ):
        """
        Inicializa un Doser.

        Args:
            name: Nombre del doser
            assigned_silo_ids: IDs de los silos asignados
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
                f"La tasa de dosificación inicial ({current_rate}) está fuera del rango permitido ({dosing_range})."
            )

        silo_ids = tuple(assigned_silo_ids)
        if not silo_ids:
            raise ValueError("Doser debe tener al menos un silo asignado")
        if len(set(silo_ids)) != len(silo_ids):
            raise ValueError("Doser no puede tener silos asignados duplicados")

        self._id = DoserId.from_string(_existing_id) if _existing_id else DoserId.generate()
        self._name = name
        self._assigned_silo_ids = silo_ids
        self._doser_type = doser_type
        self._dosing_range = dosing_range
        self._current_rate = current_rate
        self._is_on = is_on
        self._speed_percentage = speed_percentage
        self.calibrated_grams_per_second = calibrated_grams_per_second
        self.pulse_on_time = pulse_on_time
        self.pulse_off_time = pulse_off_time
        self.pulse_speed = pulse_speed
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
    def assigned_silo_ids(self) -> Tuple[SiloId, ...]:
        return self._assigned_silo_ids

    @assigned_silo_ids.setter
    def assigned_silo_ids(self, new_silo_ids: Tuple[SiloId, ...]) -> None:
        if not new_silo_ids:
            raise ValueError("Doser debe tener al menos un silo asignado")
        if len(set(new_silo_ids)) != len(new_silo_ids):
            raise ValueError("Doser no puede tener silos asignados duplicados")
        self._assigned_silo_ids = tuple(new_silo_ids)

    @property
    def assigned_silo_id(self) -> SiloId:
        """Compatibilidad interna: retorna el primer silo asignado."""
        return self._assigned_silo_ids[0]

    @assigned_silo_id.setter
    def assigned_silo_id(self, new_silo_id: SiloId) -> None:
        self.assigned_silo_ids = (new_silo_id,)

    @property
    def doser_type(self) -> DoserType:
        return self._doser_type

    @property
    def dosing_range(self) -> DosingRange:
        return self._dosing_range

    @dosing_range.setter
    def dosing_range(self, new_range: DosingRange) -> None:
        # TODO Cuando exista calibración comprobar que el nuevo rango
        # TODO incluye la tasa actual
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
    def calibrated_grams_per_second(self) -> Optional[float]:
        """Caudal calibrado explícito en gramos por segundo."""
        return self._calibrated_grams_per_second

    @calibrated_grams_per_second.setter
    def calibrated_grams_per_second(self, value: Optional[float]) -> None:
        if value is not None and value <= 0:
            raise ValueError("calibrated_grams_per_second debe ser mayor que 0")
        self._calibrated_grams_per_second = value

    @property
    def pulse_on_time(self) -> Optional[float]:
        """Tiempo activo de cada pulso en segundos."""
        return self._pulse_on_time

    @pulse_on_time.setter
    def pulse_on_time(self, value: Optional[float]) -> None:
        if value is not None and value <= 0:
            raise ValueError("pulse_on_time debe ser mayor que 0")
        self._pulse_on_time = value

    @property
    def pulse_off_time(self) -> Optional[float]:
        """Tiempo de pausa entre pulsos en segundos."""
        return self._pulse_off_time

    @pulse_off_time.setter
    def pulse_off_time(self, value: Optional[float]) -> None:
        if value is not None and value < 0:
            raise ValueError("pulse_off_time no puede ser negativo")
        self._pulse_off_time = value

    @property
    def pulse_speed(self) -> Optional[int]:
        """Velocidad usada para pulsos de calibración (1-100)."""
        return self._pulse_speed

    @pulse_speed.setter
    def pulse_speed(self, value: Optional[int]) -> None:
        if value is not None and not (1 <= value <= 100):
            raise ValueError(f"pulse_speed debe estar entre 1 y 100, recibido: {value}")
        self._pulse_speed = value

    @property
    def is_on(self) -> bool:
        """Indica si el doser está encendido."""
        return self._is_on

    @property
    def max_rate_kg_per_min(self) -> float:
        """Tasa máxima de dosificación en kg/min."""
        return self._dosing_range.max_rate

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
