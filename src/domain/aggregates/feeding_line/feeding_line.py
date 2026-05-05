from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple, cast

from ...enums import FeedingLineStatus
from ...exceptions import (
    DuplicateSensorTypeException,
    FeedingLineUnavailableException,
    InsufficientComponentsException,
)
from ...interfaces import IBlower, ICooler, IDoser, ISelector, ISensor
from ...value_objects import LineId, LineName, SensorId


class FeedingLine:
    def __init__(
        self,
        name: LineName,
        status: FeedingLineStatus = FeedingLineStatus.AVAILABLE,
        locked_by: Optional[str] = None,
        locked_reason: Optional[str] = None,
        locked_at: Optional[datetime] = None,
    ):
        self._id = LineId.generate()
        self._name = name
        self._status = status
        self._locked_by = locked_by
        self._locked_reason = locked_reason
        self._locked_at = locked_at
        self._blower: Optional[IBlower] = None
        self._dosers: Tuple[IDoser, ...] = ()
        self._selector: Optional[ISelector] = None
        self._sensors: Tuple[ISensor, ...] = ()
        self._cooler: Optional[ICooler] = None
        self._created_at = datetime.now(timezone.utc)

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
    def status(self) -> FeedingLineStatus:
        return self._status

    @property
    def locked_by(self) -> Optional[str]:
        return self._locked_by

    @property
    def locked_reason(self) -> Optional[str]:
        return self._locked_reason

    @property
    def locked_at(self) -> Optional[datetime]:
        return self._locked_at

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

    def reserve_for_feeding(self, operator_id: Optional[str] = None) -> None:
        """Reserva la línea para una sesión de alimentación."""
        self._assert_available("iniciar alimentación")
        self._set_lock(
            status=FeedingLineStatus.FEEDING,
            locked_by=operator_id,
            locked_reason="feeding",
        )

    def release_from_feeding(self) -> None:
        """Libera la línea si estaba reservada por alimentación."""
        if self._status == FeedingLineStatus.FEEDING:
            self._clear_lock()

    def acquire_manual_control(
        self,
        operator_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Bloquea la línea para manipulación manual directa de dispositivos."""
        self._assert_available("tomar control manual")
        self._set_lock(
            status=FeedingLineStatus.MANUAL_CONTROL,
            locked_by=operator_id,
            locked_reason=reason or "manual_control",
        )

    def release_manual_control(self) -> None:
        """Libera la línea si estaba bloqueada por control manual."""
        if self._status != FeedingLineStatus.MANUAL_CONTROL:
            raise FeedingLineUnavailableException(
                f"No se puede liberar control manual de una línea en estado {self._status.value}"
            )
        self._clear_lock()

    def send_to_maintenance(
        self,
        operator_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        self._set_lock(
            status=FeedingLineStatus.MAINTENANCE,
            locked_by=operator_id,
            locked_reason=reason or "maintenance",
        )

    def mark_fault(
        self,
        operator_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        self._set_lock(
            status=FeedingLineStatus.FAULT,
            locked_by=operator_id,
            locked_reason=reason or "fault",
        )

    def mark_available(self) -> None:
        self._clear_lock()

    def require_manual_control(self) -> None:
        if self._status != FeedingLineStatus.MANUAL_CONTROL:
            raise FeedingLineUnavailableException(
                f"La línea {self._name.value} debe estar en MANUAL_CONTROL para control directo "
                f"(estado actual: {self._status.value})"
            )

    def _assert_available(self, action: str) -> None:
        if self._status != FeedingLineStatus.AVAILABLE:
            lock_detail = f" por {self._locked_by}" if self._locked_by else ""
            raise FeedingLineUnavailableException(
                f"No se puede {action}: la línea {self._name.value} está en estado "
                f"{self._status.value}{lock_detail}"
            )

    def _set_lock(
        self,
        status: FeedingLineStatus,
        locked_by: Optional[str],
        locked_reason: Optional[str],
    ) -> None:
        self._status = status
        self._locked_by = locked_by
        self._locked_reason = locked_reason
        self._locked_at = datetime.now(timezone.utc)

    def _clear_lock(self) -> None:
        self._status = FeedingLineStatus.AVAILABLE
        self._locked_by = None
        self._locked_reason = None
        self._locked_at = None

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
