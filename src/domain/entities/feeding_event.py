import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from enum import Enum


class FeedingEventType(Enum):
    """Tipos de eventos que ocurren durante una sesión de alimentación."""
    # Eventos de sesión
    SESSION_STARTED = "session_started"
    SESSION_PAUSED = "session_paused"
    SESSION_RESUMED = "session_resumed"
    SESSION_COMPLETED = "session_completed"
    SESSION_CANCELLED = "session_cancelled"
    SESSION_INTERRUPTED = "session_interrupted"

    # Eventos de visita
    VISIT_STARTED = "visit_started"
    VISIT_COMPLETED = "visit_completed"
    VISIT_SIMULATED = "visit_simulated"

    # Eventos de configuración
    RATE_CHANGED = "rate_changed"
    CAGE_MODE_CHANGED = "cage_mode_changed"

    # Eventos de alarma y PLC
    ALARM = "alarm"
    PLC_CONNECTION_LOST = "plc_connection_lost"
    PLC_SAFE_MODE_ACTIVATED = "plc_safe_mode_activated"


class FeedingEvent:
    """
    Entidad inmutable que representa un evento durante una sesión de alimentación.
    Los eventos se registran para trazabilidad y auditoría.
    """
    def __init__(
        self,
        feeding_session_id: str,
        event_type: FeedingEventType,
        data: Dict[str, Any],
    ):
        self._id = str(uuid.uuid4())
        self._feeding_session_id = feeding_session_id

        if not isinstance(event_type, FeedingEventType):
            raise ValueError("event_type debe ser una instancia de FeedingEventType")

        self._event_type = event_type
        self._timestamp = datetime.now(timezone.utc)
        self._data = data.copy() if data else {}

    @property
    def id(self):
        return self._id

    @property
    def feeding_session_id(self):
        return self._feeding_session_id

    @property
    def event_type(self):
        return self._event_type

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def data(self):
        return self._data.copy()

    # Factory methods para eventos de sesión

    @classmethod
    def session_started(cls, feeding_session_id: str, operator_id: str):
        """Evento de inicio de sesión."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.SESSION_STARTED,
            data={"operator_id": operator_id}
        )

    @classmethod
    def session_paused(cls, feeding_session_id: str, operator_id: str, reason: str):
        """Evento de pausa de sesión."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.SESSION_PAUSED,
            data={"operator_id": operator_id, "reason": reason}
        )

    @classmethod
    def session_resumed(cls, feeding_session_id: str, operator_id: str):
        """Evento de reanudación de sesión."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.SESSION_RESUMED,
            data={"operator_id": operator_id}
        )

    @classmethod
    def session_completed(cls, feeding_session_id: str, total_dispensed_kg: float, duration_seconds: float):
        """Evento de sesión completada."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.SESSION_COMPLETED,
            data={
                "total_dispensed_kg": total_dispensed_kg,
                "duration_seconds": duration_seconds
            }
        )

    @classmethod
    def session_cancelled(cls, feeding_session_id: str, operator_id: str, reason: str):
        """Evento de sesión cancelada."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.SESSION_CANCELLED,
            data={"operator_id": operator_id, "reason": reason}
        )

    @classmethod
    def session_interrupted(cls, feeding_session_id: str, reason: str, pending_visits: int):
        """Evento de sesión interrumpida (por error, pérdida de conexión, etc)."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.SESSION_INTERRUPTED,
            data={"reason": reason, "pending_visits": pending_visits}
        )

    # Factory methods para eventos de visita

    @classmethod
    def visit_started(
        cls,
        feeding_session_id: str,
        cage_id: str,
        visit_number: int,
        cycle_number: int
    ):
        """Evento de inicio de visita a una jaula."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.VISIT_STARTED,
            data={
                "cage_id": cage_id,
                "visit_number": visit_number,
                "cycle_number": cycle_number
            }
        )

    @classmethod
    def visit_completed(
        cls,
        feeding_session_id: str,
        cage_id: str,
        visit_number: int,
        cycle_number: int,
        dispensed_grams: float,
        duration_seconds: float
    ):
        """Evento de visita completada."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.VISIT_COMPLETED,
            data={
                "cage_id": cage_id,
                "visit_number": visit_number,
                "cycle_number": cycle_number,
                "dispensed_grams": dispensed_grams,
                "duration_seconds": duration_seconds
            }
        )

    @classmethod
    def visit_simulated(
        cls,
        feeding_session_id: str,
        cage_id: str,
        visit_number: int,
        cycle_number: int,
        simulated_duration_seconds: float
    ):
        """Evento de visita simulada (modo PAUSE)."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.VISIT_SIMULATED,
            data={
                "cage_id": cage_id,
                "visit_number": visit_number,
                "cycle_number": cycle_number,
                "simulated_duration_seconds": simulated_duration_seconds
            }
        )

    # Factory methods para eventos de configuración

    @classmethod
    def rate_changed(
        cls,
        feeding_session_id: str,
        cage_id: str,
        previous_rate: float,
        new_rate: float,
        applied_immediately: bool
    ):
        """Evento de cambio de tasa de alimentación."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.RATE_CHANGED,
            data={
                "cage_id": cage_id,
                "previous_rate": previous_rate,
                "new_rate": new_rate,
                "applied_immediately": applied_immediately
            }
        )

    @classmethod
    def cage_mode_changed(
        cls,
        feeding_session_id: str,
        cage_id: str,
        previous_mode: str,
        new_mode: str
    ):
        """Evento de cambio de modo de jaula (NORMAL/PAUSE/FASTING)."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.CAGE_MODE_CHANGED,
            data={
                "cage_id": cage_id,
                "previous_mode": previous_mode,
                "new_mode": new_mode
            }
        )

    # Factory methods para eventos de alarma y PLC

    @classmethod
    def alarm_triggered(
        cls,
        feeding_session_id: str,
        alarm_type: str,
        sensor_value: float,
        threshold: float
    ):
        """Evento de alarma activada."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.ALARM,
            data={
                "alarm_type": alarm_type,
                "sensor_value": sensor_value,
                "threshold": threshold
            }
        )

    @classmethod
    def plc_connection_lost(cls, feeding_session_id: str):
        """Evento de pérdida de conexión con el PLC."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.PLC_CONNECTION_LOST,
            data={}
        )

    @classmethod
    def plc_safe_mode_activated(cls, feeding_session_id: str, reason: str):
        """Evento de activación de modo seguro del PLC."""
        return cls(
            feeding_session_id=feeding_session_id,
            event_type=FeedingEventType.PLC_SAFE_MODE_ACTIVATED,
            data={"reason": reason}
        )
