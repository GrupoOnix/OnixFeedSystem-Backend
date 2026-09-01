from datetime import time

import pytest

from domain.aggregates.system_config import SystemConfig


def test_updates_sensor_thresholds() -> None:
    config = SystemConfig.create_default()

    config.update(
        feeding_start_time=time(6, 0),
        feeding_end_time=time(18, 0),
        timezone_id="America/Santiago",
        temperature_warning_threshold=65.0,
        temperature_critical_threshold=80.0,
        pressure_warning_threshold=1.1,
        pressure_critical_threshold=1.4,
        flow_warning_threshold=16.0,
        flow_critical_threshold=20.0,
    )

    assert config.temperature_warning_threshold == 65.0
    assert config.temperature_critical_threshold == 80.0
    assert config.pressure_warning_threshold == 1.1
    assert config.pressure_critical_threshold == 1.4
    assert config.flow_warning_threshold == 16.0
    assert config.flow_critical_threshold == 20.0


def test_rejects_critical_sensor_threshold_not_above_warning() -> None:
    config = SystemConfig.create_default()

    with pytest.raises(ValueError, match="crítico de temperatura"):
        config.update(
            feeding_start_time=time(6, 0),
            feeding_end_time=time(18, 0),
            timezone_id="America/Santiago",
            temperature_warning_threshold=85.0,
            temperature_critical_threshold=85.0,
        )
