"""
Aggregate Root: FeedingSession
Representa una sesión operativa diaria de alimentación.
"""

from dataclasses import asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from domain.events import FeedingEvent
from domain.entities import FeedingOperation
from domain.strategies.base import IFeedingStrategy
from domain.value_objects import LineId, SessionId, Weight, CageId, OperationId
from domain.interfaces import IFeedingMachine
from domain.dtos import MachineStatus
from domain.enums import FeedingEventType, SessionStatus, OperationStatus


def _serialize_for_json(obj: Any) -> Any:
    """
    Serializa recursivamente un objeto para que sea JSON-safe.
    Convierte Enums a sus valores string.
    """
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    else:
        return obj


class FeedingSession:
    """
    Aggregate Root que representa una sesión operativa diaria.
    Mantiene acumuladores globales y referencia a la operación actual.
    """

    def __init__(self, line_id: LineId):
        self._id: SessionId = SessionId.generate()
        self._line_id: LineId = line_id
        self._date: datetime = datetime.utcnow()
        self._status: SessionStatus = SessionStatus.ACTIVE  # Siempre ACTIVE al crear

        # Acumuladores globales del día
        self._total_dispensed_kg: Weight = Weight.zero()
        self._dispensed_by_slot: Dict[int, Weight] = {}

        # Operación actual (la clave del cambio)
        # NO mantenemos lista completa de operaciones en memoria
        self._current_operation: Optional[FeedingOperation] = None

        # Eventos a nivel de sesión
        self._session_events: List[FeedingEvent] = []

    # Properties
    @property
    def id(self) -> SessionId:
        return self._id

    @property
    def line_id(self) -> LineId:
        return self._line_id

    @property
    def date(self) -> datetime:
        return self._date

    @property
    def status(self) -> SessionStatus:
        return self._status

    @property
    def total_dispensed_kg(self) -> Weight:
        return self._total_dispensed_kg

    @property
    def dispensed_by_slot(self) -> Dict[int, Weight]:
        return self._dispensed_by_slot.copy()

    @property
    def current_operation(self) -> Optional[FeedingOperation]:
        return self._current_operation

    # Métodos de negocio
    async def start_operation(
        self, cage_id: CageId, target_slot: int, strategy: IFeedingStrategy, machine: IFeedingMachine
    ) -> OperationId:
        """Inicia una nueva operación de alimentación."""

        # Validar que no haya operación activa
        if self._current_operation is not None:
            if self._current_operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
                raise ValueError(
                    f"Ya hay una operación activa (status: {self._current_operation.status}). Debes hacer STOP primero."
                )

        # Obtener configuración del PLC
        config_dto = strategy.get_plc_configuration()
        config_dict = asdict(config_dto)
        config_serialized = _serialize_for_json(config_dict)

        # Crear nueva operación
        operation = FeedingOperation(
            session_id=self._id,
            cage_id=cage_id,
            target_slot=target_slot,
            target_amount=Weight.from_kg(config_dto.target_amount_kg),
            applied_config=config_serialized,
        )

        # Inicializar contador de slot si no existe
        if target_slot not in self._dispensed_by_slot:
            self._dispensed_by_slot[target_slot] = Weight.zero()

        # Enviar configuración al PLC
        await machine.send_configuration(self._line_id, config_dto)

        # Registrar operación como actual
        self._current_operation = operation

        # Log a nivel de sesión
        self._log_session_event(
            FeedingEventType.COMMAND,
            f"Nueva operación iniciada en jaula {cage_id}",
            {"operation_id": str(operation.id), "target_kg": config_dto.target_amount_kg},
        )

        return operation.id

    async def stop_current_operation(self, machine: IFeedingMachine) -> None:
        """Finaliza la operación actual (cierra la visita)."""

        if self._current_operation is None:
            return  # Idempotente

        # Detener PLC
        await machine.stop(self._line_id)

        # Cerrar operación
        self._current_operation.stop()

        # Log a nivel de sesión
        self._log_session_event(
            FeedingEventType.COMMAND,
            f"Operación finalizada: {self._current_operation.dispensed.as_kg}kg",
            {"operation_id": str(self._current_operation.id)},
        )

        # Liberar slot (la sesión sigue ACTIVE)
        self._current_operation = None

    async def pause_current_operation(self, machine: IFeedingMachine) -> None:
        """Pausa temporalmente la operación actual."""

        if self._current_operation is None:
            raise ValueError("No hay operación activa para pausar")

        if self._current_operation.status != OperationStatus.RUNNING:
            raise ValueError("Solo se puede pausar una operación RUNNING")

        await machine.pause(self._line_id)
        self._current_operation.pause()

    async def resume_current_operation(self, machine: IFeedingMachine) -> None:
        """Reanuda la operación pausada."""

        if self._current_operation is None:
            raise ValueError("No hay operación para reanudar")

        if self._current_operation.status != OperationStatus.PAUSED:
            raise ValueError("Solo se puede reanudar una operación PAUSED")

        await machine.resume(self._line_id)
        self._current_operation.resume()

    async def update_current_operation_params(self, new_strategy: IFeedingStrategy, machine: IFeedingMachine) -> None:
        """Actualiza parámetros de la operación actual en caliente."""

        if self._current_operation is None:
            raise ValueError("No hay operación activa")

        if self._current_operation.status != OperationStatus.RUNNING:
            raise ValueError("Solo se pueden cambiar parámetros en RUNNING")

        # Obtener nueva configuración
        new_config_dto = new_strategy.get_plc_configuration()
        old_config = self._current_operation.applied_config

        # Detectar cambios
        changes = {}
        if new_config_dto.blower_speed_percentage != old_config.get("blower_speed_percentage"):
            changes["blower_speed"] = {
                "from": old_config.get("blower_speed_percentage"),
                "to": new_config_dto.blower_speed_percentage,
            }
        if new_config_dto.doser_speed_percentage != old_config.get("doser_speed_percentage"):
            changes["doser_speed"] = {
                "from": old_config.get("doser_speed_percentage"),
                "to": new_config_dto.doser_speed_percentage,
            }

        # Aplicar
        config_dict = asdict(new_config_dto)
        config_serialized = _serialize_for_json(config_dict)

        await machine.send_configuration(self._line_id, new_config_dto)
        self._current_operation.update_config(config_serialized, changes)

    def update_from_plc(self, plc_status: MachineStatus) -> None:
        """Sincroniza estado desde el PLC (heartbeat). PENDIENTE DE IMPLEMENTACIÓN COMPLETA."""

        if self._current_operation is None:
            return

        # Calcular delta
        new_total = plc_status.total_dispensed_kg
        current_total = self._total_dispensed_kg.as_kg
        delta_kg = new_total - current_total

        if delta_kg > 0:
            delta_weight = Weight.from_kg(delta_kg)

            # Actualizar operación actual
            self._current_operation.add_dispensed_amount(delta_weight)

            # Actualizar acumuladores de sesión
            slot = self._current_operation.target_slot
            self._dispensed_by_slot[slot] += delta_weight
            self._total_dispensed_kg += delta_weight

        # Sincronizar estado (simplificado por ahora)
        if plc_status.has_error:
            if self._current_operation.status != OperationStatus.FAILED:
                self._current_operation.fail(str(plc_status.error_code) if plc_status.error_code else "unknown")

    def close_session(self) -> None:
        """Cierra la sesión al final del día."""
        if self._current_operation is not None:
            raise ValueError("No se puede cerrar sesión con operación activa")

        self._status = SessionStatus.CLOSED
        self._log_session_event(FeedingEventType.SYSTEM_STATUS, "Sesión cerrada (fin del día)")

    def _log_session_event(self, type: FeedingEventType, description: str, details: Optional[Dict[str, Any]] = None):
        event = FeedingEvent(timestamp=datetime.utcnow(), type=type, description=description, details=details or {})
        self._session_events.append(event)

    def pop_events(self) -> List[FeedingEvent]:
        events = self._session_events.copy()
        self._session_events.clear()
        return events

    def get_daily_summary(self) -> Dict[str, Any]:
        """
        Genera un reporte simple del estado actual de la sesión.
        """
        return {
            "session_id": str(self._id),
            "date": self._date.isoformat(),
            "status": self._status.value,
            "total_kg": self._total_dispensed_kg.as_kg,
            "details_by_slot": {slot: weight.as_kg for slot, weight in self._dispensed_by_slot.items()},
            "current_operation": {
                "operation_id": str(self._current_operation.id),
                "cage_id": str(self._current_operation.cage_id),
                "status": self._current_operation.status.value,
                "dispensed_kg": self._current_operation.dispensed.as_kg,
                "target_kg": self._current_operation.target_amount.as_kg,
            }
            if self._current_operation
            else None,
        }
