"""
Aggregate Root: Alert
Representa una alerta del sistema.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from domain.enums import AlertCategory, AlertStatus, AlertType
from domain.value_objects import AlertId


class Alert:
    """
    Aggregate Root que representa una alerta del sistema.

    Las alertas pueden ser generadas por:
    - Triggers automáticos (nivel bajo de silo, sensor fuera de rango, etc.)
    - Alertas programadas (mantenimiento)
    - Eventos del sistema
    """

    def __init__(
        self,
        type: AlertType,
        category: AlertCategory,
        title: str,
        message: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self._id: AlertId = AlertId.generate()
        self._type: AlertType = type
        self._status: AlertStatus = AlertStatus.UNREAD
        self._category: AlertCategory = category
        self._title: str = title
        self._message: str = message
        self._source: Optional[str] = source
        self._timestamp: datetime = datetime.now(timezone.utc)
        self._read_at: Optional[datetime] = None
        self._resolved_at: Optional[datetime] = None
        self._resolved_by: Optional[str] = None
        self._snoozed_until: Optional[datetime] = None
        self._metadata: Dict[str, Any] = metadata.copy() if metadata else {}

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def id(self) -> AlertId:
        return self._id

    @property
    def type(self) -> AlertType:
        return self._type

    @property
    def status(self) -> AlertStatus:
        return self._status

    @property
    def category(self) -> AlertCategory:
        return self._category

    @property
    def title(self) -> str:
        return self._title

    @property
    def message(self) -> str:
        return self._message

    @property
    def source(self) -> Optional[str]:
        return self._source

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def read_at(self) -> Optional[datetime]:
        return self._read_at

    @property
    def resolved_at(self) -> Optional[datetime]:
        return self._resolved_at

    @property
    def resolved_by(self) -> Optional[str]:
        return self._resolved_by

    @property
    def snoozed_until(self) -> Optional[datetime]:
        return self._snoozed_until

    @property
    def is_snoozed(self) -> bool:
        """Indica si la alerta está actualmente silenciada."""
        if self._snoozed_until is None:
            return False
        return datetime.now(timezone.utc) < self._snoozed_until

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata.copy()

    # =========================================================================
    # Métodos de negocio
    # =========================================================================

    def mark_as_read(self) -> None:
        """Marca la alerta como leída."""
        if self._status == AlertStatus.UNREAD:
            self._status = AlertStatus.READ
            self._read_at = datetime.now(timezone.utc)

    def resolve(self, resolved_by: Optional[str] = None) -> None:
        """
        Resuelve la alerta.

        Args:
            resolved_by: Usuario que resuelve la alerta (opcional por ahora).
        """
        if self._status in [AlertStatus.UNREAD, AlertStatus.READ]:
            self._status = AlertStatus.RESOLVED
            self._resolved_at = datetime.now(timezone.utc)
            self._resolved_by = resolved_by
            # Si no estaba leída, marcarla como leída también
            if self._read_at is None:
                self._read_at = self._resolved_at

    def archive(self) -> None:
        """Archiva la alerta."""
        self._status = AlertStatus.ARCHIVED

    def snooze(self, duration_days: int) -> None:
        """
        Silencia la alerta por un período de tiempo.

        La alerta no aparecerá en las consultas hasta que expire el snooze.
        Útil para alertas de nivel bajo de silos que están en proceso de recarga.

        Args:
            duration_days: Duración del silenciamiento en días (1 o 7 típicamente)
        """
        from datetime import timedelta

        if duration_days <= 0:
            raise ValueError("La duración del snooze debe ser mayor a 0 días")

        self._snoozed_until = datetime.now(timezone.utc) + timedelta(days=duration_days)

    def unsnooze(self) -> None:
        """Remueve el silenciamiento de la alerta."""
        self._snoozed_until = None

    def update_content(
        self,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        type: Optional[AlertType] = None,
    ) -> None:
        """
        Actualiza el contenido de la alerta.

        Útil para actualizar alertas existentes en lugar de crear duplicados.
        Por ejemplo, actualizar el porcentaje de nivel de un silo.

        Args:
            message: Nuevo mensaje (opcional)
            metadata: Nuevos metadatos (se combinan con los existentes)
            type: Nuevo tipo de alerta (opcional, para cambiar de WARNING a CRITICAL)
        """
        if message is not None:
            self._message = message

        if metadata is not None:
            self._metadata.update(metadata)

        if type is not None:
            self._type = type

        # Actualizar timestamp para reflejar la actualización
        self._timestamp = datetime.now(timezone.utc)

        # Si la alerta estaba resuelta, volver a marcarla como no leída
        # (porque el problema persiste o empeoró)
        if self._status in [AlertStatus.RESOLVED, AlertStatus.READ]:
            self._status = AlertStatus.UNREAD
            self._read_at = None
            self._resolved_at = None
            self._resolved_by = None

        # Si la alerta estaba silenciada y se actualiza, remover el snooze
        # (el problema cambió, el usuario debe ver la actualización)
        if self._snoozed_until is not None:
            self._snoozed_until = None

    def update_status(self, new_status: AlertStatus) -> None:
        """
        Actualiza el estado de la alerta.

        Validaciones:
        - No se puede volver a UNREAD una vez leída
        - ARCHIVED es un estado final (no se puede cambiar)
        """
        if self._status == AlertStatus.ARCHIVED:
            raise ValueError("No se puede cambiar el estado de una alerta archivada")

        if new_status == AlertStatus.UNREAD and self._status != AlertStatus.UNREAD:
            raise ValueError("No se puede marcar como no leída una alerta ya procesada")

        old_status = self._status
        self._status = new_status

        # Actualizar timestamps según el nuevo estado
        if new_status == AlertStatus.READ and old_status == AlertStatus.UNREAD:
            self._read_at = datetime.now(timezone.utc)
        elif new_status == AlertStatus.RESOLVED:
            self._resolved_at = datetime.now(timezone.utc)
            if self._read_at is None:
                self._read_at = self._resolved_at

    # =========================================================================
    # Métodos de reconstrucción (para el repositorio)
    # =========================================================================

    @classmethod
    def reconstitute(
        cls,
        id: AlertId,
        type: AlertType,
        status: AlertStatus,
        category: AlertCategory,
        title: str,
        message: str,
        timestamp: datetime,
        source: Optional[str] = None,
        read_at: Optional[datetime] = None,
        resolved_at: Optional[datetime] = None,
        resolved_by: Optional[str] = None,
        snoozed_until: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Alert":
        """
        Reconstruye una alerta desde la base de datos.
        Usado por el repositorio para rehidratar el aggregate.
        """
        alert = cls.__new__(cls)
        alert._id = id
        alert._type = type
        alert._status = status
        alert._category = category
        alert._title = title
        alert._message = message
        alert._source = source
        alert._timestamp = timestamp
        alert._read_at = read_at
        alert._resolved_at = resolved_at
        alert._resolved_by = resolved_by
        alert._snoozed_until = snoozed_until
        alert._metadata = metadata or {}
        return alert
