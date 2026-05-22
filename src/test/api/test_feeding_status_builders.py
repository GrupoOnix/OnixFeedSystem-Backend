from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.models.feeding_models import CageConfigInput, CyclicFeedingRequest
from api.helpers.feeding_status_builders import _calculate_pulse_metrics


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
