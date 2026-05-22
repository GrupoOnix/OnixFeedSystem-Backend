from datetime import datetime, timezone
from math import ceil
from typing import Dict, Any, Optional

from domain.aggregates.feeding_line.doser import Doser
from domain.entities.cage_feeding import CageFeedingMode
from domain.entities.feeding_session import FeedingSession
from domain.value_objects import CageId, LineId
from infrastructure.persistence.repositories.cage_feeding_repository import CageFeedingRepository
from infrastructure.persistence.repositories.feeding_line_repository import FeedingLineRepository
from infrastructure.persistence.repositories.cage_repository import CageRepository
from infrastructure.services.simulated_machine import SimulatedMachine


LIVE_SESSION_STATUSES = {"IN_PROGRESS", "PAUSED"}


def _calculate_pulse_metrics(
    programmed_kg_per_visit: float,
    programmed_visits: int,
    doser: Optional[Doser],
) -> Dict[str, Optional[float | int]]:
    if (
        not doser
        or doser.calibrated_grams_per_second is None
        or doser.pulse_on_time is None
    ):
        return {
            "grams_per_pulse": None,
            "pulses_per_visit": None,
            "estimated_pulses_total": None,
        }

    grams_per_pulse = doser.calibrated_grams_per_second * doser.pulse_on_time
    if grams_per_pulse <= 0 or programmed_kg_per_visit <= 0:
        return {
            "grams_per_pulse": None,
            "pulses_per_visit": None,
            "estimated_pulses_total": None,
        }

    pulses_per_visit = ceil((programmed_kg_per_visit * 1000) / grams_per_pulse)
    return {
        "grams_per_pulse": round(grams_per_pulse, 3),
        "pulses_per_visit": pulses_per_visit,
        "estimated_pulses_total": pulses_per_visit * programmed_visits,
    }


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

    live_dispensed = (
        machine_status.dispensed_kg
        if session.status.value in LIVE_SESSION_STATUSES and current_cf.status.value == "IN_PROGRESS"
        else current_cf.dispensed_kg
    )
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
    line_repo: FeedingLineRepository,
    machine: SimulatedMachine
) -> Dict[str, Any]:
    cf_list = await cage_feeding_repo.find_by_session(session.id)
    if not cf_list:
        raise ValueError("No hay cage feedings para esta sesión")

    machine_status = await machine.get_status(LineId.from_string(session.line_id))
    line = await line_repo.find_by_id(LineId.from_string(session.line_id))
    doser_by_id = {
        str(doser.id): doser
        for doser in (line.dosers if line else ())
    }

    active_cfs = [cf for cf in cf_list if cf.mode != CageFeedingMode.FASTING]
    total_rounds = max((cf.programmed_visits for cf in active_cfs), default=0)
    total_cages = len(active_cfs)
    active_cf = next(
        (cf for cf in cf_list
         if cf.mode != CageFeedingMode.FASTING
         and cf.status.value == "IN_PROGRESS"),
        None,
    ) if session.status.value in LIVE_SESSION_STATUSES else None

    if session.status.value == "COMPLETED":
        current_round = total_rounds
    elif active_cf:
        current_round = min(active_cf.completed_visits + 1, total_rounds)
    elif active_cfs:
        current_round = min(
            max((cf.completed_visits for cf in active_cfs), default=0) + 1,
            total_rounds,
        )
    else:
        current_round = 0

    total_dispensed_kg = sum(cf.dispensed_kg for cf in cf_list)
    if active_cf:
        total_dispensed_kg += machine_status.dispensed_kg
    overall_completion_percentage = (
        (total_dispensed_kg / session.total_programmed_kg * 100)
        if session.total_programmed_kg > 0
        else 0.0
    )

    active_cage_info = None
    if active_cf:
        cage = await cage_repo.find_by_id(CageId.from_string(active_cf.cage_id))
        cage_name = cage.name.value if cage else active_cf.cage_id

        current_visit_number = active_cf.completed_visits + 1
        current_visit_dispensed_kg = machine_status.dispensed_kg
        current_visit_programmed_kg = active_cf.programmed_kg
        current_visit_completion_percentage = (
            (current_visit_dispensed_kg / current_visit_programmed_kg * 100)
            if current_visit_programmed_kg > 0
            else 0.0
        )
        active_pulse_metrics = _calculate_pulse_metrics(
            programmed_kg_per_visit=current_visit_programmed_kg,
            programmed_visits=active_cf.programmed_visits,
            doser=doser_by_id.get(active_cf.doser_id),
        )

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
            "programmed_kg_per_visit": current_visit_programmed_kg,
            "current_visit_completion_percentage": round(current_visit_completion_percentage, 2),
            "current_flow_rate_kg_per_min": machine_status.current_flow_rate_kg_per_min,
            **active_pulse_metrics,
        }

    cage_name_cache = {}
    cages_summary = []
    for cf in cf_list:
        if cf.cage_id not in cage_name_cache:
            cage = await cage_repo.find_by_id(CageId.from_string(cf.cage_id))
            cage_name_cache[cf.cage_id] = cage.name.value if cage else cf.cage_id

        programmed_kg_per_visit = cf.programmed_kg
        total_programmed_kg_for_cage = programmed_kg_per_visit * cf.programmed_visits
        total_dispensed_kg_for_cage = cf.dispensed_kg
        if active_cf and cf.id == active_cf.id:
            total_dispensed_kg_for_cage += machine_status.dispensed_kg

        overall_completion_percentage_cage = (
            (total_dispensed_kg_for_cage / total_programmed_kg_for_cage * 100)
            if total_programmed_kg_for_cage > 0
            else 0.0
        )
        pulse_metrics = _calculate_pulse_metrics(
            programmed_kg_per_visit=programmed_kg_per_visit,
            programmed_visits=cf.programmed_visits,
            doser=doser_by_id.get(cf.doser_id),
        )

        cages_summary.append({
            "cage_id": cf.cage_id,
            "cage_name": cage_name_cache[cf.cage_id],
            "mode": cf.mode.value,
            "status": cf.status.value,
            "execution_order": cf.execution_order,
            "programmed_kg_per_visit": programmed_kg_per_visit,
            "total_programmed_kg": total_programmed_kg_for_cage,
            "total_dispensed_kg": round(total_dispensed_kg_for_cage, 3),
            "programmed_visits": cf.programmed_visits,
            "completed_visits": cf.completed_visits,
            "overall_completion_percentage": round(overall_completion_percentage_cage, 2),
            **pulse_metrics,
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
