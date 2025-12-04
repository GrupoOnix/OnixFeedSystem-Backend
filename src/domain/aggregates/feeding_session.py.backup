from dataclasses import asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from domain.events import FeedingEvent
from domain.strategies.base import IFeedingStrategy
from domain.value_objects import LineId, SessionId, Weight
from domain.interfaces import IFeedingMachine
from domain.dtos import MachineStatus
from domain.enums import FeedingEventType, SessionStatus


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
    Aggregate Root que representa una sesión operativa de alimentación (un día de trabajo).
    
    Responsabilidades:
    1. Mantener el estado acumulado del día (Total Kgs).
    2. Coordinar el inicio de la alimentación enviando la configuración al PLC.
    3. Actualizar su estado basado en el feedback del PLC (Polling).
    4. Ser la fuente de verdad para el reporte diario.
    5. Registrar eventos de auditoría (logs) de todas las acciones relevantes.
    """

    def __init__(self, line_id: LineId):
        self._id: SessionId = SessionId.generate()
        self._line_id: LineId = line_id
        self._date: datetime = datetime.utcnow() # Fecha de creación (el "Día")
        
        self._status: SessionStatus = SessionStatus.CREATED
        
        self._total_dispensed_kg: Weight = Weight.zero()

        # NUEVO: Acumuladores por Slot Físico {slot_number: Weight}
        # Ejemplo: {1: Weight(5.0), 2: Weight(5.0)}
        self._dispensed_by_slot: Dict[int, Weight] = {}
        
        self._applied_strategy_config: Optional[Dict[str, Any]] = None 
        
        # Cola de eventos nuevos para guardar en repositorio
        self._new_events: List[FeedingEvent] = []

    # -------------------------------------------------------
    # Propiedades (Lectura)
    # -------------------------------------------------------
    
    @property
    def id(self) -> SessionId:
        """Identificador único de la sesión."""
        return self._id

    @property
    def line_id(self) -> LineId:
        """Referencia a la línea física donde ocurre la sesión."""
        return self._line_id

    @property
    def date(self) -> datetime:
        """Fecha de creación de la sesión."""
        return self._date

    @property
    def status(self) -> SessionStatus:
        """Estado actual de la sesión."""
        return self._status

    @property
    def total_dispensed_kg(self) -> Weight:
        """Cantidad total de alimento entregado en esta sesión (día)."""
        return self._total_dispensed_kg

    @property
    def dispensed_by_slot(self) -> Dict[int, Weight]:
        """Retorna una copia del desglose por slot."""
        return self._dispensed_by_slot.copy()

    @property
    def applied_strategy_config(self) -> Optional[Dict[str, Any]]:
        """Configuración de estrategia aplicada actualmente."""
        return self._applied_strategy_config

    # -------------------------------------------------------
    # Métodos Privados de Logging
    # -------------------------------------------------------

    def _log(self, type: FeedingEventType, description: str, details: Dict[str, Any] = None) -> None:
        """Registra un evento interno en la cola de nuevos eventos."""
        event = FeedingEvent(
            timestamp=datetime.utcnow(),
            type=type,
            description=description,
            details=details or {}
        )
        self._new_events.append(event)

    def pop_events(self) -> List[FeedingEvent]:
        """Devuelve y limpia la lista de eventos nuevos para ser persistidos."""
        events = self._new_events.copy()
        self._new_events.clear()
        return events

    # -------------------------------------------------------
    # Comportamiento de Negocio (Métodos Públicos)
    # -------------------------------------------------------

    async def start(self, strategy: IFeedingStrategy, machine: IFeedingMachine) -> None:
        """
        Inicia (o reinicia) la alimentación aplicando una estrategia.
        La estrategia determina qué jaulas alimentar (puede ser una o múltiples).
        """
        # 1. Solicitar a la estrategia la configuración técnica (MachineConfiguration)
        # La estrategia ya conoce internamente qué slots/jaulas alimentar
        config_dto = strategy.get_plc_configuration()
        
        # 2. Guardar un snapshot de qué pedimos hacer (Auditoría)
        # Usar serialización custom para convertir Enums a valores string
        config_dict = asdict(config_dto)
        self._applied_strategy_config = _serialize_for_json(config_dict)

        # Inicializamos los contadores en 0 para los slots que vamos a usar
        # Esto ayuda a que el reporte muestre las jaulas pendientes con 0kg
        for slot in config_dto.slot_numbers:
            if slot not in self._dispensed_by_slot:
                self._dispensed_by_slot[slot] = Weight.zero()
        
        # 3. Enviar esa configuración al PLC (Fuego)
        await machine.send_configuration(self._line_id, config_dto)
        
        # 4. Actualizar estado local inmediatamente (Optimismo)
        # El polling confirmará esto después, pero la intención ya es RUNNING
        self._status = SessionStatus.RUNNING
        
        # Loguear evento de inicio
        self._log(FeedingEventType.COMMAND, "Inicio de Alimentación", {
            "mode": config_dto.mode.value,  # Usar .value para serializar el Enum
            "target_kg": config_dto.target_amount_kg,
            "slots": config_dto.slot_numbers
        })

    async def stop(self, machine: IFeedingMachine) -> None:
        """
        Detiene la alimentación inmediatamente.
        """
        # 1. Enviar comando de parada al PLC
        await machine.stop(self._line_id)
        
        # 2. Actualizar estado
        # Marcamos como PAUSED para indicar que se detuvo manual o forzosamente,
        # permitiendo reanudar si fuera necesario. Si terminó un ciclo completo,
        # update_from_plc lo cambiará a COMPLETED.
        self._status = SessionStatus.PAUSED
        
        # Loguear evento de parada
        self._log(FeedingEventType.COMMAND, "Detención Manual (Stop)", {
            "final_kg": self._total_dispensed_kg.as_kg
        })

    async def pause(self, machine: IFeedingMachine) -> None:
        """
        Pausa explícita: Congela el PLC y actualiza estado lógico.
        """
        # 1. Delegar al hardware
        await machine.pause(self._line_id)
        # 2. Actualizar estado lógico (Optimista)
        self._status = SessionStatus.PAUSED
        
        # Loguear evento de pausa
        self._log(FeedingEventType.COMMAND, "Pausa Manual", {
            "kg_at_pause": self._total_dispensed_kg.as_kg
        })

    async def resume(self, machine: IFeedingMachine) -> None:
        """
        Reanudar: Descongela el PLC y actualiza estado lógico.
        """
        # 1. Delegar al hardware
        await machine.resume(self._line_id)
        # 2. Actualizar estado lógico (Optimista)
        self._status = SessionStatus.RUNNING
        
        # Loguear evento de reanudación
        self._log(FeedingEventType.COMMAND, "Reanudación Manual")

    async def update_parameters(self, new_strategy: IFeedingStrategy, machine: IFeedingMachine) -> None:
        """
        Actualiza parámetros en caliente (Hot Swap) sin detener la alimentación.
        """
        if self._status != SessionStatus.RUNNING:
            # Nota: Podría permitirse en PAUSED también, depende de la regla de negocio.
            # Por seguridad, asumimos solo RUNNING por ahora.
            raise ValueError("Solo se pueden cambiar parámetros mientras corre.")

        new_config_dto = new_strategy.get_plc_configuration()
        old_config = self._applied_strategy_config or {}
        
        # Detectar cambios para log
        changes = {}
        if new_config_dto.blower_speed_percentage != old_config.get('blower_speed_percentage'):
            changes['blower_speed'] = {
                'from': old_config.get('blower_speed_percentage'), 
                'to': new_config_dto.blower_speed_percentage
            }
        
        if new_config_dto.doser_speed_percentage != old_config.get('doser_speed_percentage'):
            changes['doser_speed'] = {
                'from': old_config.get('doser_speed_percentage'), 
                'to': new_config_dto.doser_speed_percentage
            }

        # Actualizar snapshot y enviar
        # Usar serialización custom para convertir Enums a valores string
        config_dict = asdict(new_config_dto)
        self._applied_strategy_config = _serialize_for_json(config_dict)
        await machine.send_configuration(self._line_id, new_config_dto)
        
        if changes:
            self._log(FeedingEventType.PARAM_CHANGE, "Cambio de parámetros en caliente", changes)

    def update_from_plc(self, plc_status: MachineStatus) -> None:
        """
        Sincroniza estado y distribuye el consumo al slot actual.
        """
        # 1. Calcular el incremento (Delta) desde la última lectura
        # Si es la primera lectura, el delta es el total reportado.
        new_total_val = plc_status.total_dispensed_kg
        current_total_val = self._total_dispensed_kg.as_kg
        
        delta_val = new_total_val - current_total_val
        
        # Solo procesamos si hubo aumento (evita problemas si el PLC reinicia contadores)
        if delta_val > 0:
            # 2. Identificar a quién cobrarle este alimento
            current_slot = plc_status.current_slot_number
            
            # Asegurar que el slot existe en el diccionario
            if current_slot not in self._dispensed_by_slot:
                self._dispensed_by_slot[current_slot] = Weight.zero()
            
            # 3. Sumar al slot específico
            # CORRECCIÓN: Convertir el delta (float) a Weight antes de sumar
            # Esto es necesario porque Weight.__add__ espera otro objeto Weight
            delta_weight = Weight.from_kg(delta_val)
            self._dispensed_by_slot[current_slot] += delta_weight
            
            # 4. Actualizar el total global
            self._total_dispensed_kg = Weight.from_kg(new_total_val)

        # 5. Sincronizar Estado (Igual que antes)
        if plc_status.is_running:
            self._status = SessionStatus.RUNNING
        elif plc_status.is_paused:
            self._status = SessionStatus.PAUSED
        else:
            # Si no está corriendo ni pausado explícitamente, está detenido/completado
            # Solo cambiamos a COMPLETED si veníamos de estar RUNNING/PAUSED
            if self._status in [SessionStatus.RUNNING, SessionStatus.PAUSED]:
                self._status = SessionStatus.COMPLETED
                # Loguear fin automático
                self._log(FeedingEventType.SYSTEM_STATUS, "Fin Automático de Ciclo (Reportado por PLC)", {
                    "total_kg": self._total_dispensed_kg.as_kg
                })
        
        # (Opcional) Aquí podrías detectar errores reportados por plc_status.error_code
        if plc_status.has_error:
            # Solo loguear si no estábamos ya en failed para no spamear logs
            if self._status != SessionStatus.FAILED:
                self._log(FeedingEventType.ALARM, f"Falla reportada por PLC", {"code": plc_status.error_code})
            self._status = SessionStatus.FAILED

    def get_daily_summary(self) -> Dict[str, Any]:
        """
        Genera un reporte simple del estado actual de la sesión.
        """
        return {
            "session_id": str(self._id),
            "date": self._date.isoformat(),
            "status": self._status.value,
            "total_kg": self._total_dispensed_kg.as_kg,
            # Agregamos el detalle para que el frontend pinte las barras de progreso
            "details_by_slot": {
                slot: weight.as_kg 
                for slot, weight in self._dispensed_by_slot.items()
            },
            # El mode ya está serializado como string en applied_strategy_config
            "mode": self._applied_strategy_config.get("mode") if self._applied_strategy_config else None
        }