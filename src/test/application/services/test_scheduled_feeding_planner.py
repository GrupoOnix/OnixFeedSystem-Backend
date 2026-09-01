from datetime import datetime
from types import SimpleNamespace
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from api.models.feeding_models import ScheduledFeedingPlanRequest
from application.services.scheduled_feeding_planner import (
    ScheduledFeedingPlanner,
    _allocate_proportional_pulses,
    _uniform_schedule,
)
from infrastructure.persistence.models.scheduled_feeding_plan_model import (
    ScheduledFeedingPlanModel,
)


class _Repository:
    def __init__(self, result):
        self.result = result

    async def find_by_id(self, _identifier):
        return self.result


class _RepositoryById:
    def __init__(self, results):
        self.results = results

    async def find_by_id(self, identifier):
        return self.results[str(identifier.value)]

    async def find_by_cage(self, identifier):
        return self.results[str(identifier.value)]


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


def _planner(*, transport_time_seconds: float | None = 5.0, grams_per_second: float = 100.0):
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
        calibrated_grams_per_second=grams_per_second,
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
    assert result.estimated_total_seconds == 3600
    assert result.remaining_seconds == 0
    assert result.wait_after_visit_seconds > 0
    assert result.cage_plans[0].planned_pulses == 10
    assert sum(result.cage_plans[0].pulse_schedule) == 10
    assert sum(result.cage_plans[0].quantity_schedule_kg) == 1.0


@pytest.mark.asyncio
async def test_planner_does_not_limit_rounds_to_two_hundred():
    planner, request = _planner(grams_per_second=1.0)

    result = await planner.calculate(request)

    assert result.total_rounds == 266
    assert len(result.cage_plans[0].pulse_schedule) == 266


@pytest.mark.asyncio
async def test_planner_rejects_a_cage_without_transport_time():
    planner, request = _planner(transport_time_seconds=None)

    with pytest.raises(ValueError, match="tiempo de transporte"):
        await planner.calculate(request)


@pytest.mark.asyncio
async def test_planner_excludes_fasting_cage_target_from_totals_and_timing():
    line_id, group_id, doser_id, silo_id, normal_cage_id, fasting_cage_id = (uuid4() for _ in range(6))
    line = SimpleNamespace(
        blower=SimpleNamespace(
            blow_before_feeding_time=SimpleNamespace(value=0),
            blow_after_feeding_time=SimpleNamespace(value=0),
        )
    )
    normal_cage = SimpleNamespace(
        id=_identifier(normal_cage_id), name="Jaula normal",
        config=SimpleNamespace(transport_time_seconds=5.0),
    )
    fasting_cage = SimpleNamespace(
        id=_identifier(fasting_cage_id), name="Jaula en ayuno",
        config=SimpleNamespace(transport_time_seconds=None),
    )
    doser = SimpleNamespace(
        assigned_silo_ids=[_identifier(silo_id)], calibrated_grams_per_second=100.0,
        pulse_on_time=1.0, pulse_off_time=1.0, max_rate_kg_per_min=5.0,
    )
    planner = ScheduledFeedingPlanner(
        line_repository=_Repository(line),
        cage_repository=_RepositoryById({
            str(normal_cage_id): normal_cage,
            str(fasting_cage_id): fasting_cage,
        }),
        cage_group_repository=_Repository(SimpleNamespace(cage_ids=[
            _identifier(normal_cage_id), _identifier(fasting_cage_id),
        ])),
        doser_repository=_DoserRepository(SimpleNamespace(line_id=line_id, doser=doser)),
        silo_repository=_Repository(SimpleNamespace(available_stock=SimpleNamespace(as_kg=1.0))),
        slot_assignment_repository=_RepositoryById({
            str(normal_cage_id): SimpleNamespace(line_id=_identifier(line_id), slot_number=1),
            str(fasting_cage_id): SimpleNamespace(line_id=_identifier(line_id), slot_number=2),
        }),
        selector_positioning_seconds=1.0,
    )
    request = ScheduledFeedingPlanRequest.model_validate({
        "name": "Plan con ayuno", "line_id": str(line_id), "group_id": str(group_id),
        "doser_id": str(doser_id), "silo_id": str(silo_id), "start_time": "08:00",
        "end_time": "09:00", "timezone": "America/Santiago",
        "cage_configs": [
            {"cage_id": str(normal_cage_id), "mode": "NORMAL", "daily_target_kg": 1.0},
            {"cage_id": str(fasting_cage_id), "mode": "FASTING", "daily_target_kg": 10.0},
        ],
    })

    result = await planner.calculate(request)

    assert result.total_requested_kg == 1.0
    assert result.total_planned_kg == 1.0
    assert result.cage_plans[1].requested_kg == 0
    assert result.cage_plans[1].planned_pulses == 0
    assert result.cage_plans[1].pulse_schedule == [0] * result.total_rounds
    assert result.estimated_total_seconds == 3600


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


@pytest.mark.asyncio
async def test_execution_reconstructs_daily_targets_from_saved_cage_plans():
    planner, request = _planner()
    calculated = await planner.calculate(request)
    plan = ScheduledFeedingPlanModel(
        line_id=UUID(request.line_id),
        group_id=UUID(request.group_id),
        doser_id=UUID(request.doser_id),
        silo_id=UUID(request.silo_id),
        name=request.name,
        start_time=request.start_time,
        end_time=request.end_time,
        timezone=request.timezone,
        blower_power_percentage=request.blower_power_percentage,
        wait_after_visit_seconds=calculated.wait_after_visit_seconds,
        total_rounds=calculated.total_rounds,
        total_requested_kg=calculated.total_requested_kg,
        total_planned_kg=calculated.total_planned_kg,
        estimated_total_seconds=calculated.estimated_total_seconds,
        cage_plans=[cage_plan.model_dump() for cage_plan in calculated.cage_plans],
    )

    result = await planner.calculate_execution(
        plan,
        now=datetime(2026, 8, 31, 8, 0, tzinfo=ZoneInfo("America/Santiago")),
    )

    assert result.cage_plans[0].requested_kg == 1.0
