"""
Entidad FeedingOperation - Representa una operación atómica de alimentación.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

from domain.enums import OperationStatus, OperationEventType
from domain.value_objects import CageId, Weight, OperationId, SessionId


@dataclass
class OperationEvent:
    """Evento específico de una operación."""
    timestamp: datetime
    type: OperationEventType
    description: str
    details: Dict[str, Any]


class FeedingOperation:
    """
    Entity que representa una operación atómica de alimentación.
    Una "visita" a una jaula desde START hasta STOP.
    """

    def __init__(
        self,
        session_id: SessionId,
        cage_id: CageId,
        target_slot: int,
        target_amount: Weight,
        applied_config: Dict[str, Any]
    ):
        self._id: OperationId = OperationId.generate()
        self._session_id: SessionId = session_id  # Necesario para persistencia
        self._cage_id: CageId = cage_id
        self._target_slot: int = target_slot
        self._target_amount: Weight = target_amount
        self._dispensed: Weight = Weight.zero()
        self._status: OperationStatus = OperationStatus.RUNNING
        self._started_at: datetime = datetime.utcnow()
        self._ended_at: Optional[datetime] = None
        self._applied_config: Dict[str, Any] = applied_config
        self._events: List[OperationEvent] = []
        self._new_events: List[OperationEvent] = []  # Cola de eventos nuevos

        self._log_event(
            OperationEventType.STARTED,
            f"Operación iniciada en jaula {cage_id}",
            {"target_kg": target_amount.as_kg, "slot": target_slot}
        )

    # Properties
    @property
    def id(self) -> OperationId:
        return self._id

    @property
    def session_id(self) -> SessionId:
        return self._session_id

    @property
    def cage_id(self) -> CageId:
        return self._cage_id

    @property
    def target_slot(self) -> int:
        return self._target_slot

    @property
    def target_amount(self) -> Weight:
        return self._target_amount

    @property
    def dispensed(self) -> Weight:
        return self._dispensed

    @property
    def status(self) -> OperationStatus:
        return self._status

    @property
    def started_at(self) -> datetime:
        return self._started_at

    @property
    def ended_at(self) -> Optional[datetime]:
        return self._ended_at

    @property
    def applied_config(self) -> Dict[str, Any]:
        return self._applied_config.copy()

    @property
    def events(self) -> List[OperationEvent]:
        """Retorna todos los eventos (para reconstrucción desde BD)."""
        return self._events.copy()

    # Métodos de negocio
    def _log_event(self, type: OperationEventType, description: str, details: Dict[str, Any] = None):
        event = OperationEvent(
            timestamp=datetime.utcnow(),
            type=type,
            description=description,
            details=details or {}
        )
        self._events.append(event)
        self._new_events.append(event)  # También a la cola de nuevos

    def pop_new_events(self) -> List[OperationEvent]:
        """Devuelve y limpia la cola de eventos nuevos para persistir."""
        events = self._new_events.copy()
        self._new_events.clear()
        return events

    def pause(self):
        if self._status != OperationStatus.RUNNING:
            raise ValueError("Solo se puede pausar una operación RUNNING")
        self._status = OperationStatus.PAUSED
        self._log_event(OperationEventType.PAUSED, f"Pausado en {self._dispensed.as_kg}kg")

    def resume(self):
        if self._status != OperationStatus.PAUSED:
            raise ValueError("Solo se puede reanudar una operación PAUSED")
        self._status = OperationStatus.RUNNING
        self._log_event(OperationEventType.RESUMED, "Operación reanudada")

    def update_config(self, new_config: Dict[str, Any], changes: Dict[str, Any]):
        if self._status != OperationStatus.RUNNING:
            raise ValueError("Solo se pueden cambiar parámetros en RUNNING")
        self._applied_config = new_config
        self._log_event(OperationEventType.PARAM_CHANGE, "Parámetros actualizados", changes)

    def add_dispensed_amount(self, delta: Weight):
        """Incrementa la cantidad dispensada (llamado desde sync con PLC)."""
        self._dispensed += delta

    def complete(self):
        """Marca la operación como completada (fin automático)."""
        if self._status in [OperationStatus.COMPLETED, OperationStatus.STOPPED]:
            return  # Idempotente

        self._status = OperationStatus.COMPLETED
        self._ended_at = datetime.utcnow()
        self._log_event(
            OperationEventType.COMPLETED,
            f"Operación completada: {self._dispensed.as_kg}kg de {self._target_amount.as_kg}kg",
            {"dispensed": self._dispensed.as_kg, "target": self._target_amount.as_kg}
        )

    def stop(self):
        """Marca la operación como detenida manualmente."""
        if self._status in [OperationStatus.COMPLETED, OperationStatus.STOPPED]:
            return  # Idempotente

        self._status = OperationStatus.STOPPED
        self._ended_at = datetime.utcnow()
        self._log_event(
            OperationEventType.STOPPED,
            f"Operación detenida: {self._dispensed.as_kg}kg de {self._target_amount.as_kg}kg",
            {"dispensed": self._dispensed.as_kg, "target": self._target_amount.as_kg}
        )

    def fail(self, error_code: str):
        """Marca la operación como fallida."""
        self._status = OperationStatus.FAILED
        self._ended_at = datetime.utcnow()
        self._log_event(OperationEventType.FAILED, "Operación fallida", {"error_code": error_code})
