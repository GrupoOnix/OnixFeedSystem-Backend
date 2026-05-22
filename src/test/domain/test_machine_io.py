import pytest

from domain.dtos.machine_io import MachineCommand


def test_machine_command_allows_zero_target_with_zero_rate_for_empty_visit():
    command = MachineCommand(
        slot_number=1,
        target_kg=0,
        doser_rate_kg_per_min=0,
        blower_power_percentage=70,
        transport_time_seconds=10,
        blow_before_seconds=0,
        blow_after_seconds=0,
    )

    assert command.target_kg == 0
    assert command.doser_rate_kg_per_min == 0


def test_machine_command_requires_positive_rate_when_target_is_positive():
    with pytest.raises(ValueError, match="doser_rate_kg_per_min"):
        MachineCommand(
            slot_number=1,
            target_kg=10,
            doser_rate_kg_per_min=0,
            blower_power_percentage=70,
            transport_time_seconds=10,
            blow_before_seconds=0,
            blow_after_seconds=0,
        )
