import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from domain.dtos.machine_io import MachineCommand, MachineVisitStatus, VisitStage
from domain.interfaces import IMachine
from domain.value_objects.identifiers import LineId

logger = logging.getLogger(__name__)


@dataclass
class _LineState:
    is_running: bool = False
    is_paused: bool = False
    slot_number: int = 0
    target_kg: float = 0.0
    dispensed_kg: float = 0.0
    doser_rate_kg_per_min: float = 0.0
    blower_power_percentage: float = 0.0
    pre_pause_doser_rate: float = 0.0
    pre_pause_blower_power: float = 0.0
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    has_error: bool = False
    error_code: Optional[int] = None
    transport_time_seconds: float = 0.0
    blow_before_seconds: float = 0.0
    blow_after_seconds: float = 0.0
    selector_positioning_seconds: float = 5.0
    visit_start_time: Optional[datetime] = None
    dispensing_completed_time: Optional[datetime] = None


class SimulatedMachine(IMachine):

    def __init__(self):
        self._states: Dict[str, _LineState] = {}

    def _get_or_create(self, line_id: LineId) -> _LineState:
        key = str(line_id)
        if key not in self._states:
            self._states[key] = _LineState()
        return self._states[key]

    async def start_visit(self, line_id: LineId, command: MachineCommand) -> None:
        await asyncio.sleep(0.05)
        state = self._get_or_create(line_id)
        now = datetime.now(timezone.utc)
        state.is_running = True
        state.is_paused = False
        state.slot_number = command.slot_number
        state.target_kg = command.target_kg
        state.dispensed_kg = 0.0
        state.doser_rate_kg_per_min = command.doser_rate_kg_per_min
        state.blower_power_percentage = command.blower_power_percentage
        state.pre_pause_doser_rate = 0.0
        state.pre_pause_blower_power = 0.0
        state.last_update = now
        state.has_error = False
        state.error_code = None
        state.transport_time_seconds = command.transport_time_seconds
        state.blow_before_seconds = command.blow_before_seconds
        state.blow_after_seconds = command.blow_after_seconds
        state.selector_positioning_seconds = command.selector_positioning_seconds
        state.visit_start_time = now
        state.dispensing_completed_time = None
        logger.info(
            f"[SimMachine] Line {line_id}: START slot={command.slot_number} "
            f"target={command.target_kg}kg rate={command.doser_rate_kg_per_min}kg/min "
            f"selector={command.selector_positioning_seconds}s "
            f"blow_before={command.blow_before_seconds}s "
            f"transport={command.transport_time_seconds}s "
            f"blow_after={command.blow_after_seconds}s"
        )

    async def get_status(self, line_id: LineId) -> MachineVisitStatus:
        await asyncio.sleep(0.02)
        state = self._get_or_create(line_id)

        now = datetime.now(timezone.utc)
        stage = self._compute_stage(state, now)

        # Acumular kg solo durante la fase FEEDING
        if stage == VisitStage.FEEDING and not state.is_paused:
            delta_minutes = (now - state.last_update).total_seconds() / 60.0
            state.dispensed_kg += state.doser_rate_kg_per_min * delta_minutes
            state.last_update = now

            if state.dispensed_kg >= state.target_kg:
                state.dispensed_kg = state.target_kg
                state.is_running = False
                state.dispensing_completed_time = now
                logger.info(
                    f"[SimMachine] Line {line_id}: TARGET REACHED "
                    f"{state.dispensed_kg:.3f}kg"
                )
                stage = VisitStage.BLOWING_AFTER
        else:
            state.last_update = now

        flow_rate = (
            state.doser_rate_kg_per_min
            if stage == VisitStage.FEEDING and not state.is_paused
            else 0.0
        )

        return MachineVisitStatus(
            is_running=state.is_running,
            is_paused=state.is_paused,
            dispensed_kg=round(state.dispensed_kg, 3),
            current_flow_rate_kg_per_min=flow_rate,
            has_error=state.has_error,
            current_stage=stage,
            error_code=state.error_code,
        )

    def _compute_stage(self, state: "_LineState", now: datetime) -> VisitStage:
        if state.visit_start_time is None:
            return VisitStage.COMPLETED

        elapsed = (now - state.visit_start_time).total_seconds()

        # 1. Posicionamiento del selector (fijo, primero)
        if elapsed < state.selector_positioning_seconds:
            return VisitStage.POSITIONING_SELECTOR

        # 2. Soplado previo
        if elapsed < state.selector_positioning_seconds + state.blow_before_seconds:
            return VisitStage.BLOWING_BEFORE

        # 3. Dosificación activa
        if state.is_running:
            return VisitStage.FEEDING

        # 4. Soplado posterior: transport_time (pellet llega) + blow_after (limpieza)
        if state.dispensing_completed_time is not None:
            elapsed_after = (now - state.dispensing_completed_time).total_seconds()
            if elapsed_after < state.transport_time_seconds + state.blow_after_seconds:
                return VisitStage.BLOWING_AFTER

        return VisitStage.COMPLETED

    async def set_doser_rate(self, line_id: LineId, rate_kg_per_min: float) -> None:
        await asyncio.sleep(0.02)
        state = self._get_or_create(line_id)
        state.doser_rate_kg_per_min = rate_kg_per_min
        state.last_update = datetime.now(timezone.utc)
        logger.info(f"[SimMachine] Line {line_id}: DOSER RATE -> {rate_kg_per_min}kg/min")

    async def set_blower_power(self, line_id: LineId, power_percentage: float) -> None:
        await asyncio.sleep(0.02)
        state = self._get_or_create(line_id)
        state.blower_power_percentage = power_percentage
        logger.info(f"[SimMachine] Line {line_id}: BLOWER POWER -> {power_percentage}%")

    async def pause(self, line_id: LineId) -> None:
        await asyncio.sleep(0.05)
        state = self._get_or_create(line_id)
        if not state.is_running or state.is_paused:
            return

        now = datetime.now(timezone.utc)
        delta_minutes = (now - state.last_update).total_seconds() / 60.0
        state.dispensed_kg += state.doser_rate_kg_per_min * delta_minutes
        state.last_update = now

        state.pre_pause_doser_rate = state.doser_rate_kg_per_min
        state.pre_pause_blower_power = state.blower_power_percentage
        state.doser_rate_kg_per_min = 0.0
        state.is_paused = True
        logger.info(
            f"[SimMachine] Line {line_id}: PAUSED at {state.dispensed_kg:.3f}kg"
        )

    async def resume(self, line_id: LineId) -> None:
        await asyncio.sleep(0.05)
        state = self._get_or_create(line_id)
        if not state.is_running or not state.is_paused:
            return

        state.doser_rate_kg_per_min = state.pre_pause_doser_rate
        state.blower_power_percentage = state.pre_pause_blower_power
        state.last_update = datetime.now(timezone.utc)
        state.is_paused = False
        logger.info(
            f"[SimMachine] Line {line_id}: RESUMED at {state.dispensed_kg:.3f}kg"
        )

    async def stop(self, line_id: LineId) -> None:
        await asyncio.sleep(0.05)
        state = self._get_or_create(line_id)
        final_kg = state.dispensed_kg
        state.is_running = False
        state.is_paused = False
        state.doser_rate_kg_per_min = 0.0
        state.blower_power_percentage = 0.0
        logger.info(
            f"[SimMachine] Line {line_id}: STOPPED total={final_kg:.3f}kg"
        )
