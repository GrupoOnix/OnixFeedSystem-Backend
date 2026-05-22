from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.helpers.feeding_status_builders import (
    _calculate_pulse_metrics,
    build_cyclic_status,
    build_manual_status,
)
from api.models.feeding_models import CageConfigInput, CyclicFeedingRequest
from domain.dtos.machine_io import MachineVisitStatus, VisitStage
from domain.entities.cage_feeding import CageFeeding
from domain.entities.feeding_session import FeedingSession, FeedingType


class _MachineStub:
    async def get_status(self, line_id):
        return MachineVisitStatus(
            is_running=True,
            is_paused=True,
            dispensed_kg=3.5,
            current_flow_rate_kg_per_min=0.0,
            has_error=False,
            current_stage=VisitStage.FEEDING,
        )


class _CageRepoStub:
    async def find_by_id(self, cage_id):
        return None


class _CageFeedingRepoStub:
    def __init__(self, cage_feedings):
        self._cage_feedings = cage_feedings

    async def find_by_session(self, session_id):
        return self._cage_feedings


class _LineRepoStub:
    async def find_by_id(self, line_id):
        return SimpleNamespace(dosers=[])


def _paused_session_with_active_cage_feeding(feeding_type=FeedingType.MANUAL):
    session = FeedingSession(
        feeding_type=feeding_type,
        line_id=str(uuid4()),
        operator_id=str(uuid4()),
        total_programmed_kg=10.0,
    )
    session.start()
    session.pause()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id=str(uuid4()),
        doser_id=str(uuid4()),
        silo_id=str(uuid4()),
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=1,
        rate_kg_per_min=2.0,
    )
    cage_feeding.start()
    session.add_cage_feeding(cage_feeding)
    return session, cage_feeding


def test_calculate_pulse_metrics_with_calibration():
    doser = SimpleNamespace(
        calibrated_grams_per_second=12.5,
        pulse_on_time=2.0,
    )

    metrics = _calculate_pulse_metrics(
        programmed_kg_per_visit=1.2,
        programmed_visits=4,
        doser=doser,
    )

    assert metrics == {
        "grams_per_pulse": 25.0,
        "pulses_per_visit": 48,
        "estimated_pulses_total": 192,
    }


def test_calculate_pulse_metrics_without_calibration():
    doser = SimpleNamespace(
        calibrated_grams_per_second=None,
        pulse_on_time=2.0,
    )

    metrics = _calculate_pulse_metrics(
        programmed_kg_per_visit=1.2,
        programmed_visits=4,
        doser=doser,
    )

    assert metrics == {
        "grams_per_pulse": None,
        "pulses_per_visit": None,
        "estimated_pulses_total": None,
    }


@pytest.mark.asyncio
async def test_manual_status_uses_live_dispensed_when_session_is_paused():
    session, _ = _paused_session_with_active_cage_feeding()

    status = await build_manual_status(session, _CageRepoStub(), _MachineStub())

    assert status["status"] == "PAUSED"
    assert status["dispensed_kg_bd"] == 0.0
    assert status["dispensed_kg_live"] == 3.5
    assert status["completion_percentage"] == 35.0


@pytest.mark.asyncio
async def test_cyclic_status_keeps_active_cage_live_values_when_session_is_paused():
    session, cage_feeding = _paused_session_with_active_cage_feeding(FeedingType.CYCLIC)

    status = await build_cyclic_status(
        session,
        _CageFeedingRepoStub([cage_feeding]),
        _CageRepoStub(),
        _LineRepoStub(),
        _MachineStub(),
    )

    assert status["status"] == "PAUSED"
    assert status["total_dispensed_kg"] == 3.5
    assert status["overall_completion_percentage"] == 35.0
    assert status["active_cage"]["current_visit_dispensed_kg"] == 3.5
    assert status["cages_summary"][0]["total_dispensed_kg"] == 3.5
    assert status["cages_summary"][0]["overall_completion_percentage"] == 35.0


def test_cyclic_request_accepts_visits_per_cage_without_global_visits():
    request = CyclicFeedingRequest(
        line_id=str(uuid4()),
        group_id=str(uuid4()),
        doser_id=str(uuid4()),
        blower_power_percentage=70,
        operator_id=str(uuid4()),
        cage_configs=[
            CageConfigInput(
                cage_id=str(uuid4()),
                visits=15,
                quantity_kg=150,
                rate_kg_per_min=10,
                mode="NORMAL",
            ),
        ],
    )

    assert request.visits is None
    assert request.cage_configs[0].visits == 15


def test_cyclic_request_requires_per_cage_or_global_visits_for_active_cages():
    with pytest.raises(ValidationError, match="visits"):
        CyclicFeedingRequest(
            line_id=str(uuid4()),
            group_id=str(uuid4()),
            doser_id=str(uuid4()),
            blower_power_percentage=70,
            operator_id=str(uuid4()),
            cage_configs=[
                CageConfigInput(
                    cage_id=str(uuid4()),
                    quantity_kg=150,
                    rate_kg_per_min=10,
                    mode="NORMAL",
                ),
            ],
        )
