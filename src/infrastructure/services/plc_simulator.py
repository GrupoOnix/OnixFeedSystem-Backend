import asyncio
import random
from typing import Dict, Optional
from datetime import datetime

from domain.interfaces import IFeedingMachine
from domain.dtos import MachineConfiguration, MachineStatus
from domain.enums import FeedingMode
from domain.value_objects import LineId

class PLCSimulator(IFeedingMachine):
    """
    Simulador en memoria de un PLC de alimentación.
    Mantiene el estado de múltiples líneas.
    """
    
    def __init__(self):
        # Estado interno por línea: {line_id: InternalState}
        self._states: Dict[str, Dict] = {}

    def _get_or_create_state(self, line_id: LineId) -> Dict:
        key = line_id.value
        if key not in self._states:
            self._states[key] = {
                "is_running": False,
                "is_paused": False,
                "mode": FeedingMode.MANUAL,
                "total_dispensed_kg": 0.0,
                "current_slot": 0,
                "slot_list": [],
                "target_kg": 0.0,
                "blower_speed": 0.0,
                "doser_speed": 0.0,
                "last_update": datetime.utcnow()
            }
        return self._states[key]

    async def send_configuration(self, line_id: LineId, config: MachineConfiguration) -> None:
        state = self._get_or_create_state(line_id)
        
        # Simular retardo de red
        await asyncio.sleep(0.1)
        
        if config.start_command:
            state["is_running"] = True
            state["is_paused"] = False
            state["mode"] = config.mode
            state["slot_list"] = config.slot_numbers
            state["current_slot"] = config.slot_numbers[0] if config.slot_numbers else 0
            state["target_kg"] = config.target_amount_kg
            state["blower_speed"] = config.blower_speed_percentage
            state["doser_speed"] = getattr(config, 'doser_speed_percentage', 0.0)
            state["last_update"] = datetime.utcnow()
            print(f"[PLC-SIM] Line {line_id}: STARTED. Mode={config.mode}, Slots={config.slot_numbers}")
        else:
            # Stop command
            state["is_running"] = False
            state["is_paused"] = False
            print(f"[PLC-SIM] Line {line_id}: STOPPED.")

    async def get_status(self, line_id: LineId) -> MachineStatus:
        state = self._get_or_create_state(line_id)
        
        # Simular consumo si está corriendo
        now = datetime.utcnow()
        if state["is_running"] and not state["is_paused"]:
            elapsed = (now - state["last_update"]).total_seconds()
            
            # Tasa de simulación: 1 kg/min por cada 10% de velocidad (ejemplo)
            # speed 50% -> 5 kg/min -> 0.083 kg/s
            rate_kg_sec = (state["doser_speed"] / 10.0) / 60.0
            if rate_kg_sec < 0: rate_kg_sec = 0
            
            dispensed = rate_kg_sec * elapsed
            state["total_dispensed_kg"] += dispensed
            
            # Simular cambio de slot (si fuera cíclico) - Por ahora simple
            # Simular fin de meta (si no es manual 0.0)
            if state["target_kg"] > 0 and state["total_dispensed_kg"] >= state["target_kg"]:
                state["is_running"] = False
                print(f"[PLC-SIM] Line {line_id}: TARGET REACHED.")

        state["last_update"] = now
        
        return MachineStatus(
            is_running=state["is_running"],
            is_paused=state["is_paused"],
            current_mode=state["mode"],
            total_dispensed_kg=state["total_dispensed_kg"],
            current_flow_rate=0.0, # TODO: Calcular basado en velocidad
            current_slot_number=state["current_slot"],
            current_list_index=0,
            current_cycle_index=0,
            total_cycles_configured=1,
            has_error=False,
            error_code=None
        )

    async def pause(self, line_id: LineId) -> None:
        state = self._get_or_create_state(line_id)
        state["is_paused"] = True
        print(f"[PLC-SIM] Line {line_id}: PAUSED.")

    async def resume(self, line_id: LineId) -> None:
        state = self._get_or_create_state(line_id)
        state["is_paused"] = False
        state["last_update"] = datetime.utcnow() # Reset timer para no cobrar tiempo pausado
        print(f"[PLC-SIM] Line {line_id}: RESUMED.")

    async def stop(self, line_id: LineId) -> None:
        state = self._get_or_create_state(line_id)
        state["is_running"] = False
        state["is_paused"] = False
        print(f"[PLC-SIM] Line {line_id}: STOPPED (Hard).")
