"""
Aggregate Root: ScheduledAlert
Representa una alerta programada (para mantenimiento, recordatorios, etc.).
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from domain.enums import AlertCategory, AlertType, ScheduledAlertFrequency
from domain.value_objects import ScheduledAlertId


class ScheduledAlert:
    """
    Aggregate Root que representa una alerta programada.

    Las alertas programadas se disparan automáticamente según su frecuencia
    y pueden generar alertas normales cuando llega el momento.
    """

    def __init__(
        self,
        title: str,
        message: str,
        type: AlertType,
        category: AlertCategory,
        frequency: ScheduledAlertFrequency,
        next_trigger_date: datetime,
        days_before_warning: int = 0,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        custom_days_interval: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self._id: ScheduledAlertId = ScheduledAlertId.generate()
        self._title: str = title
        self._message: str = message
        self._type: AlertType = type
        self._category: AlertCategory = category
        self._frequency: ScheduledAlertFrequency = frequency
        self._next_trigger_date: datetime = next_trigger_date
        self._days_before_warning: int = days_before_warning
        self._is_active: bool = True
        self._device_id: Optional[str] = device_id
        self._device_name: Optional[str] = device_name
        self._custom_days_interval: Optional[int] = custom_days_interval
        self._metadata: Dict[str, Any] = metadata or {}
        self._created_at: datetime = datetime.utcnow()
        self._last_triggered_at: Optional[datetime] = None

        # Validación
        if (
            frequency == ScheduledAlertFrequency.CUSTOM_DAYS
            and not custom_days_interval
        ):
            raise ValueError(
                "custom_days_interval es requerido cuando frequency es CUSTOM_DAYS"
            )

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def id(self) -> ScheduledAlertId:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def message(self) -> str:
        return self._message

    @property
    def type(self) -> AlertType:
        return self._type

    @property
    def category(self) -> AlertCategory:
        return self._category

    @property
    def frequency(self) -> ScheduledAlertFrequency:
        return self._frequency

    @property
    def next_trigger_date(self) -> datetime:
        return self._next_trigger_date

    @property
    def days_before_warning(self) -> int:
        return self._days_before_warning

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def device_id(self) -> Optional[str]:
        return self._device_id

    @property
    def device_name(self) -> Optional[str]:
        return self._device_name

    @property
    def custom_days_interval(self) -> Optional[int]:
        return self._custom_days_interval

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata.copy()

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def last_triggered_at(self) -> Optional[datetime]:
        return self._last_triggered_at

    # =========================================================================
    # Métodos de negocio
    # =========================================================================

    def should_trigger(self, now: datetime) -> bool:
        """
        Determina si la alerta debe dispararse.

        Considera days_before_warning para disparar antes de la fecha objetivo.
        """
        if not self._is_active:
            return False

        # Calcular fecha efectiva de disparo
        trigger_date = self._next_trigger_date - timedelta(
            days=self._days_before_warning
        )

        if now >= trigger_date:
            # Verificar que no se haya disparado ya para esta fecha
            if self._last_triggered_at is None:
                return True
            return self._last_triggered_at < trigger_date

        return False

    def mark_triggered(self) -> None:
        """
        Marca la alerta como disparada y calcula la siguiente fecha.
        """
        self._last_triggered_at = datetime.utcnow()
        self._next_trigger_date = self._calculate_next_date()

    def _calculate_next_date(self) -> datetime:
        """
        Calcula la próxima fecha de disparo según la frecuencia.
        """
        base = self._next_trigger_date

        if self._frequency == ScheduledAlertFrequency.DAILY:
            return base + timedelta(days=1)

        elif self._frequency == ScheduledAlertFrequency.WEEKLY:
            return base + timedelta(weeks=1)

        elif self._frequency == ScheduledAlertFrequency.MONTHLY:
            # Siguiente mes, mismo día (manejando overflow de meses)
            month = base.month + 1
            year = base.year
            if month > 12:
                month = 1
                year += 1
            # Manejar días que no existen en el mes destino
            day = min(base.day, self._days_in_month(year, month))
            return base.replace(year=year, month=month, day=day)

        elif self._frequency == ScheduledAlertFrequency.CUSTOM_DAYS:
            return base + timedelta(days=self._custom_days_interval or 1)

        return base

    @staticmethod
    def _days_in_month(year: int, month: int) -> int:
        """Retorna la cantidad de días en un mes dado."""
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif month in [4, 6, 9, 11]:
            return 30
        elif month == 2:
            # Año bisiesto
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                return 29
            return 28
        return 30

    def toggle_active(self) -> bool:
        """
        Activa/desactiva la alerta programada.

        Returns:
            El nuevo estado de is_active.
        """
        self._is_active = not self._is_active
        return self._is_active

    def activate(self) -> None:
        """Activa la alerta programada."""
        self._is_active = True

    def deactivate(self) -> None:
        """Desactiva la alerta programada."""
        self._is_active = False

    def update(
        self,
        title: Optional[str] = None,
        message: Optional[str] = None,
        type: Optional[AlertType] = None,
        category: Optional[AlertCategory] = None,
        frequency: Optional[ScheduledAlertFrequency] = None,
        next_trigger_date: Optional[datetime] = None,
        days_before_warning: Optional[int] = None,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        custom_days_interval: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Actualiza los campos de la alerta programada.
        Solo actualiza los campos que no son None.
        """
        if title is not None:
            self._title = title
        if message is not None:
            self._message = message
        if type is not None:
            self._type = type
        if category is not None:
            self._category = category
        if frequency is not None:
            self._frequency = frequency
        if next_trigger_date is not None:
            self._next_trigger_date = next_trigger_date
        if days_before_warning is not None:
            self._days_before_warning = days_before_warning
        if device_id is not None:
            self._device_id = device_id
        if device_name is not None:
            self._device_name = device_name
        if custom_days_interval is not None:
            self._custom_days_interval = custom_days_interval
        if metadata is not None:
            self._metadata = metadata

        # Revalidar después de actualizar
        if (
            self._frequency == ScheduledAlertFrequency.CUSTOM_DAYS
            and not self._custom_days_interval
        ):
            raise ValueError(
                "custom_days_interval es requerido cuando frequency es CUSTOM_DAYS"
            )

    # =========================================================================
    # Métodos de reconstrucción (para el repositorio)
    # =========================================================================

    @classmethod
    def reconstitute(
        cls,
        id: ScheduledAlertId,
        title: str,
        message: str,
        type: AlertType,
        category: AlertCategory,
        frequency: ScheduledAlertFrequency,
        next_trigger_date: datetime,
        days_before_warning: int,
        is_active: bool,
        created_at: datetime,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        custom_days_interval: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        last_triggered_at: Optional[datetime] = None,
    ) -> "ScheduledAlert":
        """
        Reconstruye una alerta programada desde la base de datos.
        Usado por el repositorio para rehidratar el aggregate.
        """
        alert = cls.__new__(cls)
        alert._id = id
        alert._title = title
        alert._message = message
        alert._type = type
        alert._category = category
        alert._frequency = frequency
        alert._next_trigger_date = next_trigger_date
        alert._days_before_warning = days_before_warning
        alert._is_active = is_active
        alert._device_id = device_id
        alert._device_name = device_name
        alert._custom_days_interval = custom_days_interval
        alert._metadata = metadata or {}
        alert._created_at = created_at
        alert._last_triggered_at = last_triggered_at
        return alert
