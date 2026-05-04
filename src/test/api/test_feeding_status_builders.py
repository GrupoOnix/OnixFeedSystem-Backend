from types import SimpleNamespace

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
