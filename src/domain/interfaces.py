from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

from domain.dtos import (
    BlowerCommand,
    DoserCommand,
    MachineConfiguration,
    MachineStatus,
    SelectorCommand,
    SensorReadings,
)
from domain.enums import DoserType, SensorType
from domain.value_objects.identifiers import LineId

from .value_objects import (
    BlowDurationInSeconds,
    BlowerId,
    BlowerName,
    BlowerPowerPercentage,
    DoserId,
    DoserName,
    DosingRange,
    DosingRate,
    SelectorCapacity,
    SelectorId,
    SelectorName,
    SelectorSpeedProfile,
    SensorId,
    SensorName,
    SiloId,
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
    def validate_power_is_safe(self, power_to_check: BlowerPowerPercentage) -> bool: ...


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
    def doser_type(self) -> "DoserType": ...

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
    def sensor_type(self) -> "SensorType": ...


class IFeedingMachine(ABC):
    """
    Puerto (Interface) para la comunicación con el hardware de alimentación.
    La implementación puede ser un Simulador o un Cliente Modbus.
    """

    @abstractmethod
    async def send_configuration(
        self, line_id: LineId, config: MachineConfiguration
    ) -> None:
        """
        Envía una configuración completa al PLC.
        Debe traducir el DTO lógico a registros/señales específicas.
        """
        pass

    @abstractmethod
    async def get_status(self, line_id: LineId) -> MachineStatus:
        """
        Lee el estado actual de la máquina.
        Debe ser rápido (polling frecuente).
        """
        pass

    @abstractmethod
    async def pause(self, line_id: LineId) -> None:
        """
        Solicita una pausa explícita al PLC (congelar estado).
        """
        pass

    @abstractmethod
    async def resume(self, line_id: LineId) -> None:
        """
        Solicita reanudar la operación desde el estado pausado.
        """
        pass

    @abstractmethod
    async def stop(self, line_id: LineId) -> None:
        """
        Detiene totalmente la operación y resetea el ciclo.
        """
        pass

    @abstractmethod
    async def get_sensor_readings(self, line_id: LineId) -> SensorReadings:
        """
        Lee los valores actuales de todos los sensores de una línea.

        Retorna las lecturas en tiempo real de los sensores de temperatura,
        presión y flujo asociados a la línea especificada.

        En PLC real, esto leería los registros/tags correspondientes a cada sensor.
        En simulación, genera valores realistas basados en el estado de la máquina.
        """
        pass

    # =========================================================================
    # Control individual de dispositivos
    # =========================================================================

    @abstractmethod
    async def set_blower_power(self, command: BlowerCommand) -> None:
        """
        Establece la potencia de un blower específico.

        Args:
            command: Comando con ID, nombre del blower, línea y potencia.
        """
        pass

    @abstractmethod
    async def set_doser_rate(self, command: DoserCommand) -> None:
        """
        Establece la velocidad de un doser específico.

        Args:
            command: Comando con ID, nombre del doser, línea y velocidad.
        """
        pass

    @abstractmethod
    async def move_selector(self, command: SelectorCommand) -> None:
        """
        Mueve un selector a un slot específico o lo resetea a home.

        Args:
            command: Comando con ID, nombre del selector, línea y slot destino.
                     Si slot_number es None, resetea a posición home.
        """
        pass
