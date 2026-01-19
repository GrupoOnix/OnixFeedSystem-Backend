"""DTOs para el sistema de alertas."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# ============================================================================
# DTOs de Alertas
# ============================================================================


@dataclass
class AlertDTO:
    """DTO para representar una alerta en respuestas de API."""

    id: str
    type: str
    status: str
    category: str
    title: str
    message: str
    source: Optional[str]
    timestamp: datetime
    read_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class ListAlertsRequest:
    """Request para listar alertas con filtros."""

    status: Optional[List[str]] = None  # ["UNREAD", "READ"]
    type: Optional[List[str]] = None  # ["CRITICAL", "WARNING"]
    category: Optional[List[str]] = None  # ["DEVICE", "INVENTORY"]
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class ListAlertsResponse:
    """Response con lista de alertas."""

    alerts: List[AlertDTO]
    total: int


@dataclass
class UnreadCountResponse:
    """Response con contador de alertas no leídas."""

    count: int


@dataclass
class UpdateAlertRequest:
    """Request para actualizar una alerta."""

    status: Optional[str] = None
    resolved_by: Optional[str] = None


@dataclass
class MarkAllReadResponse:
    """Response de marcar todas como leídas."""

    count: int
    message: str


# ============================================================================
# DTOs de Alertas Programadas
# ============================================================================


@dataclass
class ScheduledAlertDTO:
    """DTO para representar una alerta programada en respuestas de API."""

    id: str
    title: str
    message: str
    type: str
    category: str
    frequency: str
    next_trigger_date: datetime
    days_before_warning: int
    is_active: bool
    device_id: Optional[str]
    device_name: Optional[str]
    custom_days_interval: Optional[int]
    metadata: Dict[str, Any]
    created_at: datetime
    last_triggered_at: Optional[datetime]


@dataclass
class CreateScheduledAlertRequest:
    """Request para crear una alerta programada."""

    title: str
    message: str
    type: str
    category: str
    frequency: str
    next_trigger_date: datetime
    days_before_warning: int = 0
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    custom_days_interval: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class UpdateScheduledAlertRequest:
    """Request para actualizar una alerta programada."""

    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    frequency: Optional[str] = None
    next_trigger_date: Optional[datetime] = None
    days_before_warning: Optional[int] = None
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    custom_days_interval: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ListScheduledAlertsResponse:
    """Response con lista de alertas programadas."""

    scheduled_alerts: List[ScheduledAlertDTO]


@dataclass
class ToggleScheduledAlertResponse:
    """Response de activar/desactivar alerta programada."""

    is_active: bool
