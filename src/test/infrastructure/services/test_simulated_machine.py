import asyncio

import pytest

from domain.dtos.machine_io import MachineCommand, VisitStage
from domain.value_objects.identifiers import LineId
from infrastructure.services.simulated_machine import SimulatedMachine


@pytest.mark.asyncio
async def test_pause_freezes_stage_timing_until_resume():
    machine = SimulatedMachine()
    line_id = LineId.generate()
    command = MachineCommand(
        slot_number=1,
        target_kg=10,
        doser_rate_kg_per_min=1,
        blower_power_percentage=70,
        transport_time_seconds=0,
        blow_before_seconds=0.4,
        blow_after_seconds=0,
        selector_positioning_seconds=0.4,
    )

    await machine.start_visit(line_id, command)
    await asyncio.sleep(0.1)
    await machine.pause(line_id)
    stage_at_pause = (await machine.get_status(line_id)).current_stage

    await asyncio.sleep(0.9)
    paused_status = await machine.get_status(line_id)

    assert stage_at_pause is VisitStage.POSITIONING_SELECTOR
    assert paused_status.is_paused is True
    assert paused_status.current_stage is stage_at_pause
    assert paused_status.dispensed_kg == 0

    await machine.resume(line_id)
    resumed_status = await machine.get_status(line_id)

    assert resumed_status.is_paused is False
    assert resumed_status.current_stage is VisitStage.POSITIONING_SELECTOR

    await machine.stop(line_id)
