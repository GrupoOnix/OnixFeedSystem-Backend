from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from api.models.feeding_models import ScheduledFeedingPlanRequest
from application.services.scheduled_feeding_planner import (
    ScheduledFeedingPlanner,
    _allocate_proportional_pulses,
    _uniform_schedule,
)


class _Repository:
    def __init__(self, result):
        self.result = result

    async def find_by_id(self, _identifier):
        return self.result


class _DoserRepository:
    def __init__(self, result):
        self.result = result

    async def find_by_id_with_context(self, _identifier):
        return self.result


class _SlotRepository:
    def __init__(self, result):
        self.result = result

    async def find_by_cage(self, _identifier):
        return self.result


def _identifier(value: UUID):
    return SimpleNamespace(value=value)


def _request(line_id: UUID, group_id: UUID, doser_id: UUID, silo_id: UUID, cage_id: UUID):
    return ScheduledFeedingPlanRequest.model_validate(
        {
            "name": "Plan diurno",
            "line_id": str(line_id),
            "group_id": str(group_id),
            "doser_id": str(doser_id),
            "silo_id": str(silo_id),
            "start_time": "08:00",
            "end_time": "09:00",
            "timezone": "America/Santiago",
            "cage_configs": [
                {"cage_id": str(cage_id), "mode": "NORMAL", "daily_target_kg": 1.0},
            ],
        }
    )


def _planner(*, transport_time_seconds: float | None = 5.0):
    line_id, group_id, doser_id, silo_id, cage_id = (uuid4() for _ in range(5))
    line = SimpleNamespace(
        blower=SimpleNamespace(
            blow_before_feeding_time=SimpleNamespace(value=0),
            blow_after_feeding_time=SimpleNamespace(value=0),
        )
    )
    group = SimpleNamespace(cage_ids=[_identifier(cage_id)])
    cage = SimpleNamespace(
        id=_identifier(cage_id),
        name="Jaula 1",
        config=SimpleNamespace(transport_time_seconds=transport_time_seconds),
    )
    doser = SimpleNamespace(
        assigned_silo_ids=[_identifier(silo_id)],
        calibrated_grams_per_second=100.0,
        pulse_on_time=1.0,
        pulse_off_time=1.0,
        max_rate_kg_per_min=5.0,
    )
    doser_context = SimpleNamespace(line_id=line_id, doser=doser)
    silo = SimpleNamespace(available_stock=SimpleNamespace(as_kg=2.0))
    slot = SimpleNamespace(line_id=_identifier(line_id), slot_number=1)
    planner = ScheduledFeedingPlanner(
        line_repository=_Repository(line),
        cage_repository=_Repository(cage),
        cage_group_repository=_Repository(group),
        doser_repository=_DoserRepository(doser_context),
        silo_repository=_Repository(silo),
        slot_assignment_repository=_SlotRepository(slot),
        selector_positioning_seconds=1.0,
    )
    return planner, _request(line_id, group_id, doser_id, silo_id, cage_id)


@pytest.mark.asyncio
async def test_planner_calculates_a_complete_normal_cage_plan():
    planner, request = _planner()

    result = await planner.calculate(request)

    assert result.timezone == "America/Santiago"
    assert result.total_requested_kg == 1.0
    assert result.total_planned_kg == 1.0
    assert result.total_rounds == 10
    assert result.window_seconds == 3600
    assert result.remaining_seconds == 0
    assert result.wait_after_visit_seconds > 0
    assert result.cage_plans[0].planned_pulses == 10
    assert sum(result.cage_plans[0].pulse_schedule) == 10
    assert sum(result.cage_plans[0].quantity_schedule_kg) == 1.0


@pytest.mark.asyncio
async def test_planner_rejects_a_cage_without_transport_time():
    planner, request = _planner(transport_time_seconds=None)

    with pytest.raises(ValueError, match="tiempo de transporte"):
        await planner.calculate(request)


def test_uniform_schedule_spreads_remainders_across_the_whole_window():
    assert _uniform_schedule(3, 10) == [0, 1, 0, 0, 0, 1, 0, 0, 1, 0]


def test_proportional_allocation_never_exceeds_capacity_or_requested_pulses():
    allocated = _allocate_proportional_pulses({"a": 10, "b": 20}, 12)

    assert allocated == {"a": 4, "b": 8}
    assert sum(allocated.values()) == 12


@pytest.mark.asyncio
async def test_execution_plan_reduces_quantity_instead_of_crossing_the_deadline():
    planner, request = _planner()

    result = await planner.calculate(
        request,
        window_seconds_override=40,
        preferred_rounds=5,
        allow_partial=True,
    )

    assert result.total_rounds == 5
    assert result.total_planned_kg == 0.5
    assert result.shortfall_kg == 0.5
    assert result.estimated_total_seconds == 40
