"""
Simulador de PLC para pruebas y desarrollo.

Este módulo proporciona un mock completo del sistema de control PLC que permite
desarrollar y probar la aplicación sin hardware real. Simula comportamiento
realista de máquinas (blowers, dosers, selectors) y facilita la transición
al PLC real.

Características:
- Simulación de estado de componentes (blowers, dosers, selectors)
- Cálculo realista de dispensado basado en velocidad
- Logging detallado para debugging
- Simulación de errores y condiciones especiales (opcional)
- Transiciones de estado suaves

Para integrar con PLC real:
1. Implementar IFeedingMachine con cliente Modbus/OPC-UA
2. Reemplazar PLCSimulator en dependencies.py
3. Mantener la misma interfaz IFeedingMachine
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from domain.dtos.machine_io_v2 import (
    BlowerCommand,
    CoolerCommand,
    DoserCommand,
    MachineConfiguration,
    MachineStatus,
    SelectorCommand,
    SensorReading,
    SensorReadings,
)
from domain.enums import FeedingMode, SensorType
from domain.interfaces import IFeedingMachine
from domain.value_objects.identifiers import LineId

logger = logging.getLogger(__name__)


class ComponentState(str, Enum):
    """Estados posibles de un componente de la máquina"""

    OFF = "off"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class BlowerState:
    """Estado simulado de un blower"""

    state: ComponentState = ComponentState.OFF
    target_speed_percentage: float = 0.0
    current_speed_percentage: float = 0.0
    uptime_seconds: float = 0.0

    def update(self, delta_seconds: float) -> None:
        """Actualiza el estado del blower (transición suave de velocidad)"""
        if self.state == ComponentState.RUNNING:
            self.uptime_seconds += delta_seconds
            # Transición suave hacia velocidad objetivo (aceleración/desaceleración)
            speed_diff = self.target_speed_percentage - self.current_speed_percentage
            if abs(speed_diff) > 0.1:
                # Acelera/desacelera a 20%/segundo
                max_change = 20.0 * delta_seconds
                change = max(-max_change, min(max_change, speed_diff))
                self.current_speed_percentage += change
            else:
                self.current_speed_percentage = self.target_speed_percentage


@dataclass
class DoserState:
    """Estado simulado de un dosificador"""

    state: ComponentState = ComponentState.OFF
    target_speed_percentage: float = 0.0
    current_speed_percentage: float = 0.0
    total_dispensed_kg: float = 0.0
    uptime_seconds: float = 0.0

    # Tasa de dispensado: kg/hora a 100% velocidad
    # Ajustar según especificaciones reales del dosificador
    max_flow_rate_kg_per_hour: float = 120.0

    def update(self, delta_seconds: float) -> None:
        """Actualiza el estado del doser y calcula dispensado"""
        if self.state == ComponentState.RUNNING:
            self.uptime_seconds += delta_seconds

            # Transición suave de velocidad
            speed_diff = self.target_speed_percentage - self.current_speed_percentage
            if abs(speed_diff) > 0.1:
                max_change = 15.0 * delta_seconds  # Más lento que blower
                change = max(-max_change, min(max_change, speed_diff))
                self.current_speed_percentage += change
            else:
                self.current_speed_percentage = self.target_speed_percentage

            # Calcular dispensado basado en velocidad actual
            flow_rate_kg_per_sec = (self.max_flow_rate_kg_per_hour / 3600.0) * (
                self.current_speed_percentage / 100.0
            )

            dispensed = flow_rate_kg_per_sec * delta_seconds
            self.total_dispensed_kg += dispensed

    @property
    def current_flow_rate_kg_per_hour(self) -> float:
        """Tasa de flujo actual en kg/hora"""
        return self.max_flow_rate_kg_per_hour * (self.current_speed_percentage / 100.0)


@dataclass
class SelectorState:
    """Estado simulado de un selector"""

    state: ComponentState = ComponentState.OFF
    current_slot: int = 0
    target_slot: int = 0
    is_moving: bool = False
    position_change_time_seconds: float = 2.0  # Tiempo para cambiar de posición
    time_in_transition: float = 0.0

    def update(self, delta_seconds: float) -> None:
        """Actualiza el estado del selector"""
        if self.is_moving:
            self.time_in_transition += delta_seconds
            if self.time_in_transition >= self.position_change_time_seconds:
                self.current_slot = self.target_slot
                self.is_moving = False
                self.time_in_transition = 0.0

    def move_to_slot(self, slot_number: int) -> None:
        """Inicia movimiento a un slot específico"""
        if slot_number != self.current_slot:
            self.target_slot = slot_number
            self.is_moving = True
            self.time_in_transition = 0.0


@dataclass
class LineState:
    """Estado completo de una línea de alimentación"""

    line_id: str
    is_running: bool = False
    is_paused: bool = False
    mode: FeedingMode = FeedingMode.MANUAL

    # Configuración actual
    slot_list: List[int] = field(default_factory=list)
    current_slot_index: int = 0
    target_amount_kg: float = 0.0
    batch_amount_kg: float = 0.0

    # Componentes
    blower: BlowerState = field(default_factory=BlowerState)
    doser: DoserState = field(default_factory=DoserState)
    selector: SelectorState = field(default_factory=SelectorState)

    # Tracking de tiempo
    last_update: datetime = field(default_factory=datetime.utcnow)
    session_start_time: Optional[datetime] = None

    # Ciclos (para modo automático multi-ciclo)
    current_cycle: int = 0
    total_cycles: int = 1

    # Errores simulados (opcional para testing)
    simulate_error: bool = False
    error_code: Optional[int] = None

    def update_all_components(self, delta_seconds: float) -> None:
        """Actualiza todos los componentes de la línea"""
        self.blower.update(delta_seconds)
        self.doser.update(delta_seconds)
        self.selector.update(delta_seconds)

    def get_current_slot(self) -> int:
        """Obtiene el slot actual"""
        if self.slot_list and self.current_slot_index < len(self.slot_list):
            return self.slot_list[self.current_slot_index]
        return 0

    def has_reached_target(self) -> bool:
        """Verifica si se alcanzó el objetivo de dispensado"""
        if self.target_amount_kg <= 0:
            return False  # Modo manual, sin objetivo
        return self.doser.total_dispensed_kg >= self.target_amount_kg


class PLCSimulator(IFeedingMachine):
    """
    Simulador completo de PLC para sistema de alimentación.

    Simula el comportamiento de:
    - Blowers (sopladores con control de velocidad)
    - Dosers (dosificadores con medición de flujo)
    - Selectors (selectores de jaula con cambio de posición)

    El simulador mantiene estado interno y actualiza componentes
    en tiempo real cuando se consulta el estado.

    Para integración con PLC real:
    - Reemplazar esta clase con implementación Modbus/OPC-UA
    - Mantener la misma interfaz IFeedingMachine
    - Los DTOs (MachineConfiguration, MachineStatus) se mantienen igual
    """

    def __init__(self, enable_detailed_logging: bool = True):
        """
        Inicializa el simulador.

        Args:
            enable_detailed_logging: Si es True, registra acciones detalladas
        """
        self._states: Dict[str, LineState] = {}
        self._detailed_logging = enable_detailed_logging

        if self._detailed_logging:
            logger.info("[PLC-SIM] Simulador de PLC inicializado")

    def _get_or_create_state(self, line_id: LineId) -> LineState:
        """Obtiene o crea el estado de una línea"""
        key = line_id.value
        if key not in self._states:
            self._states[key] = LineState(line_id=key)
            if self._detailed_logging:
                logger.debug(f"[PLC-SIM] Estado creado para línea {line_id}")
        return self._states[key]

    def _log_action(self, line_id: LineId, action: str, details: str = "") -> None:
        """Registra una acción del simulador"""
        if self._detailed_logging:
            msg = f"[PLC-SIM] Line {line_id}: {action}"
            if details:
                msg += f" | {details}"
            logger.info(msg)

    async def send_configuration(
        self, line_id: LineId, config: MachineConfiguration
    ) -> None:
        """
        Envía configuración al PLC simulado.

        En PLC real, esto traduciría el DTO a registros Modbus/tags OPC-UA.
        """
        state = self._get_or_create_state(line_id)

        # Simular latencia de red/comunicación
        await asyncio.sleep(0.05)

        if config.start_command:
            # Comando de START
            state.is_running = True
            state.is_paused = False
            state.mode = config.mode
            state.slot_list = config.slot_numbers
            state.current_slot_index = 0
            state.target_amount_kg = config.target_amount_kg
            state.batch_amount_kg = config.batch_amount_kg
            state.session_start_time = datetime.utcnow()

            # Configurar componentes
            state.blower.state = ComponentState.RUNNING
            state.blower.target_speed_percentage = config.blower_speed_percentage

            state.doser.state = ComponentState.RUNNING
            state.doser.target_speed_percentage = config.doser_speed_percentage
            state.doser.total_dispensed_kg = 0.0  # Reset contador

            state.selector.state = ComponentState.RUNNING
            if state.slot_list:
                state.selector.move_to_slot(state.slot_list[0])

            state.last_update = datetime.utcnow()

            self._log_action(
                line_id,
                "STARTED",
                f"Mode={config.mode.value}, Slots={config.slot_numbers}, "
                f"Target={config.target_amount_kg}kg, "
                f"Blower={config.blower_speed_percentage}%, "
                f"Doser={config.doser_speed_percentage}%",
            )
        else:
            # Comando de STOP
            state.is_running = False
            state.is_paused = False

            # Detener componentes
            state.blower.state = ComponentState.OFF
            state.blower.target_speed_percentage = 0.0

            state.doser.state = ComponentState.OFF
            state.doser.target_speed_percentage = 0.0

            state.selector.state = ComponentState.OFF

            self._log_action(
                line_id,
                "STOPPED",
                f"Total dispensed: {state.doser.total_dispensed_kg:.2f}kg",
            )

    async def get_status(self, line_id: LineId) -> MachineStatus:
        """
        Obtiene el estado actual del PLC simulado.

        En PLC real, esto leería registros Modbus/tags OPC-UA.
        """
        state = self._get_or_create_state(line_id)

        # Simular latencia de lectura
        await asyncio.sleep(0.02)

        # Actualizar estado de componentes basado en tiempo transcurrido
        now = datetime.utcnow()
        delta_seconds = (now - state.last_update).total_seconds()

        if state.is_running and not state.is_paused:
            state.update_all_components(delta_seconds)

            # Verificar si se alcanzó el objetivo
            if state.has_reached_target():
                state.is_running = False
                state.blower.state = ComponentState.OFF
                state.blower.target_speed_percentage = 0.0
                state.doser.state = ComponentState.OFF
                state.doser.target_speed_percentage = 0.0

                self._log_action(
                    line_id,
                    "TARGET REACHED",
                    f"Dispensed: {state.doser.total_dispensed_kg:.2f}kg",
                )

        state.last_update = now

        return MachineStatus(
            is_running=state.is_running,
            is_paused=state.is_paused,
            current_mode=state.mode,
            total_dispensed_kg=round(state.doser.total_dispensed_kg, 3),
            current_flow_rate=round(state.doser.current_flow_rate_kg_per_hour, 2),
            current_slot_number=state.selector.current_slot,
            current_list_index=state.current_slot_index,
            current_cycle_index=state.current_cycle,
            total_cycles_configured=state.total_cycles,
            has_error=state.simulate_error,
            error_code=state.error_code,
        )

    async def pause(self, line_id: LineId) -> None:
        """
        Pausa la operación (congela el estado).

        En PLC real, esto enviaría un comando de pausa.
        """
        state = self._get_or_create_state(line_id)

        await asyncio.sleep(0.05)

        if state.is_running and not state.is_paused:
            state.is_paused = True

            # En pausa, mantener blower a velocidad baja (no feeding)
            state.blower.target_speed_percentage = 20.0  # Velocidad mínima
            state.doser.target_speed_percentage = 0.0  # Detener dosificación

            self._log_action(
                line_id,
                "PAUSED",
                f"At {state.doser.total_dispensed_kg:.2f}kg dispensed",
            )

    async def resume(self, line_id: LineId) -> None:
        """
        Reanuda la operación desde pausa.

        En PLC real, esto enviaría un comando de reanudación.
        """
        state = self._get_or_create_state(line_id)

        await asyncio.sleep(0.05)

        if state.is_running and state.is_paused:
            state.is_paused = False
            state.last_update = datetime.utcnow()  # Reset timer

            # Restaurar velocidades configuradas
            # Nota: En implementación real, las velocidades deberían
            # estar guardadas antes de la pausa

            self._log_action(
                line_id, "RESUMED", f"From {state.doser.total_dispensed_kg:.2f}kg"
            )

    async def stop(self, line_id: LineId) -> None:
        """
        Detiene completamente la operación y resetea el ciclo.

        En PLC real, esto enviaría un comando de stop/abort.
        """
        state = self._get_or_create_state(line_id)

        await asyncio.sleep(0.05)

        final_dispensed = state.doser.total_dispensed_kg

        state.is_running = False
        state.is_paused = False

        # Detener todos los componentes
        state.blower.state = ComponentState.OFF
        state.blower.target_speed_percentage = 0.0
        state.blower.current_speed_percentage = 0.0

        state.doser.state = ComponentState.OFF
        state.doser.target_speed_percentage = 0.0
        state.doser.current_speed_percentage = 0.0

        state.selector.state = ComponentState.OFF

        self._log_action(
            line_id, "STOPPED (Hard)", f"Final dispensed: {final_dispensed:.2f}kg"
        )

    # ============================================================================
    # Métodos auxiliares para testing y debugging
    # ============================================================================

    def get_detailed_state(self, line_id: LineId) -> Dict:
        """
        Obtiene estado detallado de la línea (solo para debugging).
        No forma parte de la interfaz IFeedingMachine.
        """
        state = self._get_or_create_state(line_id)
        return {
            "line_id": state.line_id,
            "is_running": state.is_running,
            "is_paused": state.is_paused,
            "mode": state.mode.value,
            "blower": {
                "state": state.blower.state.value,
                "current_speed": state.blower.current_speed_percentage,
                "target_speed": state.blower.target_speed_percentage,
                "uptime": state.blower.uptime_seconds,
            },
            "doser": {
                "state": state.doser.state.value,
                "current_speed": state.doser.current_speed_percentage,
                "target_speed": state.doser.target_speed_percentage,
                "total_dispensed": state.doser.total_dispensed_kg,
                "flow_rate": state.doser.current_flow_rate_kg_per_hour,
                "uptime": state.doser.uptime_seconds,
            },
            "selector": {
                "state": state.selector.state.value,
                "current_slot": state.selector.current_slot,
                "target_slot": state.selector.target_slot,
                "is_moving": state.selector.is_moving,
            },
        }

    def simulate_error(
        self, line_id: LineId, error_code: int, enable: bool = True
    ) -> None:
        """
        Simula un error en la línea (solo para testing).
        No forma parte de la interfaz IFeedingMachine.
        """
        state = self._get_or_create_state(line_id)
        state.simulate_error = enable
        state.error_code = error_code if enable else None

        if enable:
            logger.warning(
                f"[PLC-SIM] Line {line_id}: ERROR SIMULATED - Code {error_code}"
            )

    # =========================================================================
    # Control individual de dispositivos (IFeedingMachine interface)
    # =========================================================================

    async def set_blower_power(self, command: BlowerCommand) -> None:
        """
        Establece la potencia de un blower específico.

        En PLC real, esto escribiría al registro Modbus/tag OPC-UA del blower.
        """
        # Simular latencia de comunicación
        await asyncio.sleep(0.03)

        if command.power_percentage > 0:
            action = "ENCENDIDO"
        else:
            action = "APAGADO"

        # Log visible en consola
        print(f"\n{'=' * 65}")
        print(f"[PLC] BLOWER {action}")
        print(f"  Línea:    {command.line_name} ({command.line_id[:8]}...)")
        print(f"  Blower:   {command.blower_name} ({command.blower_id[:8]}...)")
        print(f"  Potencia: {command.power_percentage:.1f}%")
        print(f"{'=' * 65}\n")

        logger.info(
            f"[PLC-SIM] BLOWER '{command.blower_name}' en '{command.line_name}': "
            f"{action} - {command.power_percentage:.1f}%"
        )

    async def set_doser_rate(self, command: DoserCommand) -> None:
        """
        Establece la velocidad de un doser específico.

        En PLC real, esto escribiría al registro Modbus/tag OPC-UA del doser.
        """
        # Simular latencia de comunicación
        await asyncio.sleep(0.03)

        if command.rate_percentage > 0:
            action = "ENCENDIDO"
        else:
            action = "APAGADO"

        # Log visible en consola
        print(f"\n{'=' * 65}")
        print(f"[PLC] DOSER {action}")
        print(f"  Línea:     {command.line_name} ({command.line_id[:8]}...)")
        print(f"  Doser:     {command.doser_name} ({command.doser_id[:8]}...)")
        print(f"  Velocidad: {command.rate_percentage:.1f}%")
        print(f"{'=' * 65}\n")

        logger.info(
            f"[PLC-SIM] DOSER '{command.doser_name}' en '{command.line_name}': "
            f"{action} - {command.rate_percentage:.1f}%"
        )

    async def move_selector(self, command: SelectorCommand) -> None:
        """
        Mueve un selector a un slot específico o lo resetea a home.

        En PLC real, esto enviaría el comando de posicionamiento al selector.
        """
        # Simular latencia de comunicación
        await asyncio.sleep(0.03)

        if command.slot_number is not None:
            action = "MOVIENDO"
            destino = f"Slot {command.slot_number}"
        else:
            action = "RESET (HOME)"
            destino = "HOME"

        # Log visible en consola
        print(f"\n{'=' * 65}")
        print(f"[PLC] SELECTOR {action}")
        print(f"  Línea:    {command.line_name} ({command.line_id[:8]}...)")
        print(f"  Selector: {command.selector_name} ({command.selector_id[:8]}...)")
        print(f"  Destino:  {destino}")
        print(f"{'=' * 65}\n")

        logger.info(
            f"[PLC-SIM] SELECTOR '{command.selector_name}' en '{command.line_name}': "
            f"{action} -> {destino}"
        )

    async def set_cooler_power(self, command: CoolerCommand) -> None:
        """
        Establece la potencia de un cooler específico.

        En PLC real, esto escribiría al registro Modbus/tag OPC-UA del cooler.
        """
        # Simular latencia de comunicación
        await asyncio.sleep(0.03)

        if command.power_percentage > 0:
            action = "ENCENDIDO"
        else:
            action = "APAGADO"

        # Log visible en consola
        print(f"\n{'=' * 65}")
        print(f"[PLC] COOLER {action}")
        print(f"  Línea:    {command.line_name} ({command.line_id[:8]}...)")
        print(f"  Cooler:   {command.cooler_name} ({command.cooler_id[:8]}...)")
        print(f"  Potencia: {command.power_percentage:.1f}%")
        print(f"{'=' * 65}\n")

        logger.info(
            f"[PLC-SIM] COOLER '{command.cooler_name}' en '{command.line_name}': "
            f"{action} - {command.power_percentage:.1f}%"
        )

    async def get_sensor_readings(self, line_id: LineId) -> SensorReadings:
        """
        Simula la lectura de sensores en tiempo real.

        Los valores varían según el estado de la máquina:
        - REPOSO (no running): Temperatura ~15°C, Presión ~0.2 bar, Flujo 0 m³/min
        - ALIMENTACIÓN (running): Temperatura ~25°C, Presión ~0.8 bar, Flujo ~15 m³/min

        Agrega variación aleatoria realista y detecta condiciones de warning/critical.

        En implementación real con PLC, esto leería registros Modbus/tags OPC-UA.
        """
        state = self._get_or_create_state(line_id)

        # Simular latencia de lectura del PLC
        await asyncio.sleep(0.02)

        # Determinar si la máquina está activa
        is_feeding = state.is_running and not state.is_paused

        # Generar lecturas simuladas para cada tipo de sensor
        timestamp = datetime.utcnow()
        readings: List[SensorReading] = []

        # === SENSOR DE TEMPERATURA ===
        if is_feeding:
            # Durante alimentación: 25°C ±2°C
            temp_value = 25.0 + random.uniform(-2.0, 2.0)
        else:
            # En reposo: 15°C ±2°C
            temp_value = 15.0 + random.uniform(-2.0, 2.0)

        temp_warning = temp_value > 70.0
        temp_critical = temp_value > 85.0

        readings.append(
            SensorReading(
                sensor_id=f"{line_id}-temp",  # ID simulado
                sensor_type=SensorType.TEMPERATURE,
                value=round(temp_value, 2),
                unit="°C",
                timestamp=timestamp,
                is_warning=temp_warning,
                is_critical=temp_critical,
            )
        )

        # === SENSOR DE PRESIÓN ===
        if is_feeding:
            # Durante alimentación: 0.8 bar ±0.05 bar
            pressure_value = 0.8 + random.uniform(-0.05, 0.05)
        else:
            # En reposo: 0.2 bar ±0.05 bar
            pressure_value = 0.2 + random.uniform(-0.05, 0.05)

        pressure_warning = pressure_value > 1.3
        pressure_critical = pressure_value > 1.5

        readings.append(
            SensorReading(
                sensor_id=f"{line_id}-pressure",  # ID simulado
                sensor_type=SensorType.PRESSURE,
                value=round(pressure_value, 3),
                unit="bar",
                timestamp=timestamp,
                is_warning=pressure_warning,
                is_critical=pressure_critical,
            )
        )

        # === SENSOR DE FLUJO ===
        if is_feeding:
            # Durante alimentación: 15 m³/min ±1.5 m³/min
            flow_value = 15.0 + random.uniform(-1.5, 1.5)
        else:
            # En reposo: 0 m³/min (puede tener pequeña oscilación por ruido)
            flow_value = random.uniform(0.0, 0.1)

        flow_warning = flow_value > 18.0
        flow_critical = flow_value > 22.0

        readings.append(
            SensorReading(
                sensor_id=f"{line_id}-flow",  # ID simulado
                sensor_type=SensorType.FLOW,
                value=round(flow_value, 2),
                unit="m³/min",
                timestamp=timestamp,
                is_warning=flow_warning,
                is_critical=flow_critical,
            )
        )

        if self._detailed_logging:
            logger.debug(
                f"[PLC-SIM] Line {line_id}: Sensor readings - "
                f"Temp={temp_value:.2f}°C, "
                f"Pressure={pressure_value:.3f}bar, "
                f"Flow={flow_value:.2f}m³/min "
                f"(feeding={is_feeding})"
            )

        return SensorReadings(
            line_id=str(line_id), readings=readings, timestamp=timestamp
        )
