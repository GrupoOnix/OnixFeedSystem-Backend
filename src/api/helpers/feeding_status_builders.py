from datetime import datetime, timezone
from typing import Dict, Any, Optional

from domain.entities.cage_feeding import CageFeedingMode
from domain.entities.feeding_session import FeedingSession
from domain.value_objects import LineId
from infrastructure.persistence.repositories.cage_feeding_repository import CageFeedingRepository
from infrastructure.services.simulated_machine import SimulatedMachine


async def build_manual_status(
    session: FeedingSession,
    machine: SimulatedMachine
) -> Dict[str, Any]:
    cf_list = session.cage_feedings
    current_cf = next((cf for cf in cf_list if cf.status.value == "IN_PROGRESS"), None)
    if not current_cf and cf_list:
        current_cf = cf_list[0]
    if not current_cf:
        raise ValueError("No hay cage feeding en esta sesión")

    machine_status = await machine.get_status(LineId.from_string(session.line_id))

    live_dispensed = machine_status.dispensed_kg if session.status.value == "IN_PROGRESS" else current_cf.dispensed_kg
    programmed = current_cf.programmed_kg
    completion = (live_dispensed / programmed * 100) if programmed > 0 else 0.0

    return {
        "session_id": session.id,
        "line_id": session.line_id,
        "type": session.type.value,
        "status": session.status.value,
        "cage_id": current_cf.cage_id,
        "programmed_kg": programmed,
        "dispensed_kg_bd": current_cf.dispensed_kg,
        "dispensed_kg_live": live_dispensed,
        "current_flow_rate_kg_per_min": machine_status.current_flow_rate_kg_per_min,
        "is_running": machine_status.is_running,
        "is_paused": machine_status.is_paused,
        "completion_percentage": round(completion, 2),
        "current_stage": machine_status.current_stage.value,
        "server_timestamp": datetime.now(timezone.utc),
    }


async def build_cyclic_status(
    session: FeedingSession,
    cage_feeding_repo: CageFeedingRepository,
    machine: SimulatedMachine
) -> Dict[str, Any]:
    cf_list = await cage_feeding_repo.find_by_session(session.id)
    if not cf_list:
        raise ValueError("No hay cage feedings para esta sesión")

    machine_status = await machine.get_status(LineId.from_string(session.line_id))

    active_cfs = [cf for cf in cf_list if cf.mode != CageFeedingMode.FASTING]
    total_rounds = max((cf.programmed_visits for cf in active_cfs), default=0)
    if session.status.value == "COMPLETED":
        current_round = total_rounds
    elif active_cfs:
        current_round = min(cf.completed_visits for cf in active_cfs) + 1
    else:
        current_round = 0

    active_cf = next(
        (cf for cf in cf_list
         if cf.mode != CageFeedingMode.FASTING
         and cf.completed_visits < current_round),
        None,
    ) if session.status.value == "IN_PROGRESS" else None

    total_dispensed_kg = sum(cf.dispensed_kg for cf in cf_list)
    live_dispensed = machine_status.dispensed_kg if active_cf else 0.0

    cages_summary = [
        {
            "cage_id": cf.cage_id,
            "mode": cf.mode.value,
            "status": cf.status.value,
            "execution_order": cf.execution_order,
            "programmed_kg": cf.programmed_kg,
            "dispensed_kg": cf.dispensed_kg,
            "programmed_visits": cf.programmed_visits,
            "completed_visits": cf.completed_visits,
            "visits_completion_percentage": round(cf.visits_completion_percentage(), 2),
            "kg_completion_percentage": round(cf.completion_percentage(), 2),
        }
        for cf in cf_list
    ]

    return {
        "session_id": session.id,
        "line_id": session.line_id,
        "type": session.type.value,
        "status": session.status.value,
        "total_programmed_kg": session.total_programmed_kg,
        "total_dispensed_kg": round(total_dispensed_kg, 3),
        "dispensed_kg_live": live_dispensed,
        "total_rounds": total_rounds,
        "current_round": current_round,
        "active_cage_id": active_cf.cage_id if active_cf else None,
        "current_flow_rate_kg_per_min": machine_status.current_flow_rate_kg_per_min,
        "is_running": machine_status.is_running,
        "is_paused": machine_status.is_paused,
        "current_stage": machine_status.current_stage.value,
        "cages_summary": cages_summary,
        "server_timestamp": datetime.now(timezone.utc),
    }
