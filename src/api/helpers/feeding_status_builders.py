from datetime import datetime, timezone
from typing import Dict, Any, Optional

from domain.entities.cage_feeding import CageFeedingMode
from domain.entities.feeding_session import FeedingSession
from domain.value_objects import CageId, LineId
from infrastructure.persistence.repositories.cage_feeding_repository import CageFeedingRepository
from infrastructure.persistence.repositories.cage_repository import CageRepository
from infrastructure.services.simulated_machine import SimulatedMachine


async def build_manual_status(
    session: FeedingSession,
    cage_repo: CageRepository,
    machine: SimulatedMachine
) -> Dict[str, Any]:
    cf_list = session.cage_feedings
    current_cf = next((cf for cf in cf_list if cf.status.value == "IN_PROGRESS"), None)
    if not current_cf and cf_list:
        current_cf = cf_list[0]
    if not current_cf:
        raise ValueError("No hay cage feeding en esta sesión")

    cage = await cage_repo.find_by_id(CageId.from_string(current_cf.cage_id))
    cage_name = cage.name.value if cage else current_cf.cage_id

    machine_status = await machine.get_status(LineId.from_string(session.line_id))

    live_dispensed = machine_status.dispensed_kg if session.status.value == "IN_PROGRESS" else current_cf.dispensed_kg
    programmed = current_cf.programmed_kg
    completion = (live_dispensed / programmed * 100) if programmed > 0 else 0.0

    return {
        "session_id": session.id,
        "line_id": session.line_id,
        "type": session.type.value,
        "status": session.status.value,
        "started_at": session.actual_start,
        "cage_id": current_cf.cage_id,
        "cage_name": cage_name,
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
    cage_repo: CageRepository,
    machine: SimulatedMachine
) -> Dict[str, Any]:
    cf_list = await cage_feeding_repo.find_by_session(session.id)
    if not cf_list:
        raise ValueError("No hay cage feedings para esta sesión")

    machine_status = await machine.get_status(LineId.from_string(session.line_id))

    active_cfs = [cf for cf in cf_list if cf.mode != CageFeedingMode.FASTING]
    total_rounds = max((cf.programmed_visits for cf in active_cfs), default=0)
    total_cages = len(active_cfs)

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
    if active_cf:
        total_dispensed_kg += machine_status.dispensed_kg
    overall_completion_percentage = (total_dispensed_kg / session.total_programmed_kg * 100) if session.total_programmed_kg > 0 else 0.0

    active_cage_info = None
    if active_cf:
        cage = await cage_repo.find_by_id(CageId.from_string(active_cf.cage_id))
        cage_name = cage.name.value if cage else active_cf.cage_id

        current_visit_number = active_cf.completed_visits + 1
        current_visit_dispensed_kg = machine_status.dispensed_kg
        current_visit_programmed_kg = active_cf.programmed_kg
        current_visit_completion_percentage = (current_visit_dispensed_kg / current_visit_programmed_kg * 100) if current_visit_programmed_kg > 0 else 0.0

        active_cage_info = {
            "cage_id": active_cf.cage_id,
            "cage_name": cage_name,
            "execution_order": active_cf.execution_order,
            "total_cages": total_cages,
            "current_visit_number": current_visit_number,
            "total_visits": active_cf.programmed_visits,
            "current_stage": machine_status.current_stage.value,
            "current_visit_dispensed_kg": round(current_visit_dispensed_kg, 3),
            "current_visit_programmed_kg": current_visit_programmed_kg,
            "current_visit_completion_percentage": round(current_visit_completion_percentage, 2),
            "current_flow_rate_kg_per_min": machine_status.current_flow_rate_kg_per_min,
        }

    cage_name_cache = {}
    cages_summary = []
    for cf in cf_list:
        if cf.cage_id not in cage_name_cache:
            cage = await cage_repo.find_by_id(CageId.from_string(cf.cage_id))
            cage_name_cache[cf.cage_id] = cage.name.value if cage else cf.cage_id

        programmed_kg_per_visit = cf.programmed_kg
        total_programmed_kg_for_cage = programmed_kg_per_visit * cf.programmed_visits
        overall_completion_percentage_cage = (cf.dispensed_kg / total_programmed_kg_for_cage * 100) if total_programmed_kg_for_cage > 0 else 0.0

        cages_summary.append({
            "cage_id": cf.cage_id,
            "cage_name": cage_name_cache[cf.cage_id],
            "mode": cf.mode.value,
            "status": cf.status.value,
            "execution_order": cf.execution_order,
            "programmed_kg_per_visit": programmed_kg_per_visit,
            "total_programmed_kg": total_programmed_kg_for_cage,
            "total_dispensed_kg": round(cf.dispensed_kg, 3),
            "programmed_visits": cf.programmed_visits,
            "completed_visits": cf.completed_visits,
            "overall_completion_percentage": round(overall_completion_percentage_cage, 2),
        })

    return {
        "session_id": session.id,
        "line_id": session.line_id,
        "type": session.type.value,
        "status": session.status.value,
        "started_at": session.actual_start,
        "total_programmed_kg": session.total_programmed_kg,
        "total_dispensed_kg": round(total_dispensed_kg, 3),
        "overall_completion_percentage": round(overall_completion_percentage, 2),
        "total_rounds": total_rounds,
        "current_round": current_round,
        "active_cage": active_cage_info,
        "cages_summary": cages_summary,
        "server_timestamp": datetime.now(timezone.utc),
    }
