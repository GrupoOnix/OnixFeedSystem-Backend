"""
Aggregate Root: Alert
Representa una alerta del sistema.
"""

from datetime import datetime
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
        self._timestamp: datetime = datetime.utcnow()
        self._read_at: Optional[datetime] = None
        self._resolved_at: Optional[datetime] = None
        self._resolved_by: Optional[str] = None
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
    def metadata(self) -> Dict[str, Any]:
        return self._metadata.copy()

    # =========================================================================
    # Métodos de negocio
    # =========================================================================

    def mark_as_read(self) -> None:
        """Marca la alerta como leída."""
        if self._status == AlertStatus.UNREAD:
            self._status = AlertStatus.READ
            self._read_at = datetime.utcnow()

    def resolve(self, resolved_by: Optional[str] = None) -> None:
        """
        Resuelve la alerta.

        Args:
            resolved_by: Usuario que resuelve la alerta (opcional por ahora).
        """
        if self._status in [AlertStatus.UNREAD, AlertStatus.READ]:
            self._status = AlertStatus.RESOLVED
            self._resolved_at = datetime.utcnow()
            self._resolved_by = resolved_by
            # Si no estaba leída, marcarla como leída también
            if self._read_at is None:
                self._read_at = self._resolved_at

    def archive(self) -> None:
        """Archiva la alerta."""
        self._status = AlertStatus.ARCHIVED

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
            self._read_at = datetime.utcnow()
        elif new_status == AlertStatus.RESOLVED:
            self._resolved_at = datetime.utcnow()
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
        alert._metadata = metadata or {}
        return alert
