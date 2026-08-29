"""Cálculo determinista de planes diarios basados en pulsos completos."""

from __future__ import annotations

import math
from dataclasses import dataclass
from uuid import UUID
from zoneinfo import ZoneInfo

from api.models.feeding_models import (
    ScheduledFeedingPlanRequest,
    ScheduledFeedingPlanResponse,
    ScheduledPlanCageResponse,
)
from domain.value_objects import CageId, CageGroupId, LineId, SiloId
from domain.services.scheduled_feeding_time import calculate_remaining_seconds, calculate_window_seconds
from infrastructure.persistence.repositories.cage_group_repository import CageGroupRepository
from infrastructure.persistence.repositories.cage_repository import CageRepository
from infrastructure.persistence.repositories.doser_repository import DoserRepository
from infrastructure.persistence.repositories.feeding_line_repository import FeedingLineRepository
from infrastructure.persistence.repositories.silo_repository import SiloRepository
from infrastructure.persistence.repositories.slot_assignment_repository import SlotAssignmentRepository


@dataclass(frozen=True)
class _CagePlan:
    cage_id: str
    cage_name: str
    mode: str
    rate_kg_per_min: float
    requested_kg: float
    grams_per_pulse: float | None
    planned_pulses: int
    planned_kg: float
    pulse_schedule: list[int]
    quantity_schedule_kg: list[float]
    transport_seconds: float


class ScheduledFeedingPlanner:
    """Calcula rondas máximas y reparte pulsos al inicio de la jornada."""

    def __init__(
        self,
        line_repository: FeedingLineRepository,
        cage_repository: CageRepository,
        cage_group_repository: CageGroupRepository,
        doser_repository: DoserRepository,
        silo_repository: SiloRepository,
        slot_assignment_repository: SlotAssignmentRepository,
        selector_positioning_seconds: float,
    ):
        self._lines = line_repository
        self._cages = cage_repository
        self._groups = cage_group_repository
        self._dosers = doser_repository
        self._silos = silo_repository
        self._slots = slot_assignment_repository
        self._selector_positioning_seconds = selector_positioning_seconds

    async def calculate(self, request: ScheduledFeedingPlanRequest) -> ScheduledFeedingPlanResponse:
        line_id = LineId.from_string(request.line_id)
        line = await self._lines.find_by_id(line_id)
        if not line:
            raise ValueError("La línea seleccionada no existe")

        group = await self._groups.find_by_id(CageGroupId.from_string(request.group_id))
        if not group:
            raise ValueError("El grupo de jaulas seleccionado no existe")

        expected_cage_ids = {str(cage_id.value) for cage_id in group.cage_ids}
        submitted_cage_ids = {config.cage_id for config in request.cage_configs}
        if expected_cage_ids != submitted_cage_ids:
            raise ValueError("El plan debe incluir exactamente las jaulas del grupo seleccionado")

        doser_context = await self._dosers.find_by_id_with_context(UUID(request.doser_id))
        if not doser_context:
            raise ValueError("El dosificador seleccionado no existe")
        if str(doser_context.line_id) != request.line_id:
            raise ValueError("El dosificador seleccionado no pertenece a la línea")
        doser = doser_context.doser
        if request.silo_id not in {str(silo_id.value) for silo_id in doser.assigned_silo_ids}:
            raise ValueError("El silo seleccionado no está asignado al dosificador")
        if doser.calibrated_grams_per_second is None or doser.pulse_on_time is None:
            raise ValueError("El dosificador requiere caudal calibrado y tiempo activo de pulso")
        if doser.pulse_off_time is None:
            raise ValueError("El dosificador requiere tiempo de pausa entre pulsos")
        grams_per_pulse = doser.calibrated_grams_per_second * doser.pulse_on_time
        if grams_per_pulse <= 0:
            raise ValueError("La calibración del dosificador no produce gramos por pulso válidos")

        silo = await self._silos.find_by_id(SiloId.from_string(request.silo_id))
        if not silo:
            raise ValueError("El silo seleccionado no existe")

        config_by_cage = {config.cage_id: config for config in request.cage_configs}
        cage_data: list[tuple[object, object]] = []
        for cage_id in group.cage_ids:
            cage = await self._cages.find_by_id(CageId.from_string(str(cage_id.value)))
            assignment = await self._slots.find_by_cage(CageId.from_string(str(cage_id.value)))
            if not cage or not assignment or str(assignment.line_id.value) != request.line_id:
                raise ValueError("Todas las jaulas del grupo deben estar asignadas a la línea")
            cage_data.append((cage, assignment))

        cage_data.sort(key=lambda item: item[1].slot_number)
        transport_by_cage: dict[str, float] = {}
        for cage, _assignment in cage_data:
            config = config_by_cage[str(cage.id.value)]
            if config.mode == "FASTING":
                continue
            transport_time = cage.config.transport_time_seconds
            if transport_time is None:
                raise ValueError(f"La jaula {cage.name} no tiene tiempo de transporte configurado")
            transport_seconds = float(transport_time)
            if transport_seconds < 0:
                raise ValueError(f"La jaula {cage.name} tiene un tiempo de transporte inválido")
            transport_by_cage[str(cage.id.value)] = transport_seconds

        preliminary: list[tuple[object, str, int, float]] = []
        for cage, _assignment in cage_data:
            config = config_by_cage[str(cage.id.value)]
            if config.mode == "FASTING":
                preliminary.append((cage, config.mode, 0, 0.0))
                continue
            if config.mode == "PAUSE":
                preliminary.append((cage, config.mode, 0, 0.0))
                continue
            if config.daily_target_kg <= 0:
                raise ValueError(f"La jaula {cage.name} necesita una meta diaria mayor que cero")
            pulses = math.ceil((config.daily_target_kg * 1000) / grams_per_pulse)
            preliminary.append((cage, config.mode, pulses, config.daily_target_kg))

        active_cages = [(cage, pulses) for cage, mode, pulses, _requested in preliminary if mode != "FASTING"]
        if not active_cages:
            raise ValueError("El plan debe tener al menos una jaula que no esté en ayuno")

        window_seconds = calculate_window_seconds(request.start_time, request.end_time)
        blow_seconds = (
            float(line.blower.blow_before_feeding_time.value) + float(line.blower.blow_after_feeding_time.value)
            if any(mode == "NORMAL" for _cage, mode, _pulses, _requested in preliminary)
            else 0.0
        )
        pulse_seconds = float(doser.pulse_on_time + doser.pulse_off_time)
        calculated_rate_kg_per_min = grams_per_pulse / pulse_seconds * 0.06
        if calculated_rate_kg_per_min > doser.max_rate_kg_per_min:
            raise ValueError("La tasa calculada desde la calibración excede la capacidad máxima del dosificador")
        fixed_pulse_seconds = sum(pulses * pulse_seconds for _cage, pulses in active_cages)
        movement_seconds_per_round = sum(
            self._selector_positioning_seconds + transport_by_cage[str(cage.id.value)] for cage, _pulses in active_cages
        )
        active_count = len(active_cages)
        round_seconds = movement_seconds_per_round + active_count * request.wait_after_visit_seconds
        available_for_rounds = window_seconds - blow_seconds - fixed_pulse_seconds + request.wait_after_visit_seconds
        max_rounds = math.floor(available_for_rounds / round_seconds) if round_seconds > 0 else 0
        total_rounds = min(max_rounds, 200)
        if total_rounds < 1:
            raise ValueError("La ventana horaria no alcanza para completar las metas con la calibración actual")

        plans: list[_CagePlan] = []
        for cage, mode, pulses, requested_kg in preliminary:
            if mode == "NORMAL":
                pulse_schedule = _front_loaded_schedule(pulses, total_rounds)
                quantity_schedule = [round(value * grams_per_pulse / 1000, 6) for value in pulse_schedule]
                planned_kg = round(pulses * grams_per_pulse / 1000, 6)
                per_pulse = grams_per_pulse
            else:
                pulse_schedule = [0] * total_rounds
                quantity_schedule = [0.0] * total_rounds
                planned_kg = 0.0
                per_pulse = None
            plans.append(
                _CagePlan(
                    cage_id=str(cage.id.value),
                    cage_name=str(cage.name),
                    mode=mode,
                    rate_kg_per_min=calculated_rate_kg_per_min if mode != "FASTING" else 0.0,
                    requested_kg=requested_kg,
                    grams_per_pulse=per_pulse,
                    planned_pulses=pulses,
                    planned_kg=planned_kg,
                    pulse_schedule=pulse_schedule,
                    quantity_schedule_kg=quantity_schedule,
                    transport_seconds=transport_by_cage.get(str(cage.id.value), 0.0),
                )
            )

        total_requested_kg = round(sum(plan.requested_kg for plan in plans), 6)
        total_planned_kg = round(sum(plan.planned_kg for plan in plans), 6)
        if silo.available_stock.as_kg < total_planned_kg:
            raise ValueError(
                f"Stock insuficiente: disponible {silo.available_stock.as_kg:.2f} kg, "
                f"planificado {total_planned_kg:.2f} kg"
            )
        estimated_total_seconds = (
            blow_seconds
            + fixed_pulse_seconds
            + total_rounds * movement_seconds_per_round
            + max(total_rounds * active_count - 1, 0) * request.wait_after_visit_seconds
        )
        return ScheduledFeedingPlanResponse(
            name=request.name,
            line_id=request.line_id,
            group_id=request.group_id,
            doser_id=request.doser_id,
            silo_id=request.silo_id,
            start_time=request.start_time,
            end_time=request.end_time,
            timezone=ZoneInfo(request.timezone).key,
            blower_power_percentage=request.blower_power_percentage,
            wait_after_visit_seconds=request.wait_after_visit_seconds,
            is_active=request.is_active,
            total_rounds=total_rounds,
            total_requested_kg=total_requested_kg,
            total_planned_kg=total_planned_kg,
            rounding_excess_kg=round(total_planned_kg - total_requested_kg, 6),
            estimated_total_seconds=round(estimated_total_seconds, 3),
            window_seconds=window_seconds,
            remaining_seconds=calculate_remaining_seconds(window_seconds, estimated_total_seconds),
            cage_plans=[
                ScheduledPlanCageResponse(
                    cage_id=plan.cage_id,
                    cage_name=plan.cage_name,
                    mode=plan.mode,
                    rate_kg_per_min=plan.rate_kg_per_min,
                    requested_kg=plan.requested_kg,
                    grams_per_pulse=plan.grams_per_pulse,
                    planned_pulses=plan.planned_pulses,
                    planned_kg=plan.planned_kg,
                    rounding_excess_kg=round(plan.planned_kg - plan.requested_kg, 6),
                    pulse_schedule=plan.pulse_schedule,
                    quantity_schedule_kg=plan.quantity_schedule_kg,
                )
                for plan in plans
            ],
        )


def _front_loaded_schedule(pulses: int, total_rounds: int) -> list[int]:
    """Distribuye pulsos desde la primera ronda y deja ceros al final."""
    base, remainder = divmod(pulses, total_rounds)
    return [base + (1 if index < remainder else 0) for index in range(total_rounds)]
