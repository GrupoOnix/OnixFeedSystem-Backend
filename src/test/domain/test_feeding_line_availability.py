import pytest

from domain.aggregates.feeding_line import FeedingLine
from domain.aggregates.feeding_line.blower import Blower
from domain.aggregates.feeding_line.doser import Doser
from domain.aggregates.feeding_line.selector import Selector
from domain.enums import DoserType, FeedingLineStatus
from domain.exceptions import FeedingLineUnavailableException
from domain.value_objects import (
    BlowDurationInSeconds,
    BlowerName,
    BlowerPowerPercentage,
    DoserName,
    DosingRange,
    DosingRate,
    LineName,
    SelectorCapacity,
    SelectorName,
    SelectorSpeedProfile,
    SiloId,
)


@pytest.fixture
def feeding_line():
    blower = Blower(
        name=BlowerName("Blower Test"),
        non_feeding_power=BlowerPowerPercentage(50.0),
        blow_before_time=BlowDurationInSeconds(10),
        blow_after_time=BlowDurationInSeconds(5),
    )
    doser = Doser(
        name=DoserName("Doser Test"),
        assigned_silo_id=SiloId.generate(),
        dosing_range=DosingRange(min_rate=0.1, max_rate=100.0),
        doser_type=DoserType.VARI_DOSER,
        current_rate=DosingRate(50.0),
    )
    selector = Selector(
        name=SelectorName("Selector Test"),
        capacity=SelectorCapacity(8),
        speed_profile=SelectorSpeedProfile(
            fast_speed=BlowerPowerPercentage(80.0),
            slow_speed=BlowerPowerPercentage(30.0),
        ),
    )
    return FeedingLine.create(
        name=LineName("Linea Test"),
        blower=blower,
        dosers=[doser],
        selector=selector,
    )


def test_does_not_start_manual_feeding_when_line_is_in_manual_control(feeding_line):
    feeding_line.acquire_manual_control(operator_id="operator")

    with pytest.raises(FeedingLineUnavailableException):
        feeding_line.reserve_for_feeding(operator_id="operator")


def test_does_not_start_cyclic_feeding_when_line_is_in_manual_control(feeding_line):
    feeding_line.acquire_manual_control(operator_id="operator")

    with pytest.raises(FeedingLineUnavailableException):
        feeding_line.reserve_for_feeding(operator_id="operator")


def test_does_not_acquire_manual_control_when_line_is_feeding(feeding_line):
    feeding_line.reserve_for_feeding(operator_id="operator")

    with pytest.raises(FeedingLineUnavailableException):
        feeding_line.acquire_manual_control(operator_id="operator")


@pytest.mark.parametrize(
    "status",
    [
        FeedingLineStatus.MANUAL_CONTROL,
        FeedingLineStatus.FEEDING,
        FeedingLineStatus.MAINTENANCE,
        FeedingLineStatus.FAULT,
    ],
)
def test_feeding_can_start_only_when_line_is_available(feeding_line, status):
    feeding_line._status = status

    with pytest.raises(FeedingLineUnavailableException):
        feeding_line.reserve_for_feeding(operator_id="operator")


def test_feeding_can_start_when_line_is_available(feeding_line):
    feeding_line.reserve_for_feeding(operator_id="operator")

    assert feeding_line.status == FeedingLineStatus.FEEDING


@pytest.mark.parametrize(
    "status",
    [
        FeedingLineStatus.MANUAL_CONTROL,
        FeedingLineStatus.FEEDING,
        FeedingLineStatus.MAINTENANCE,
        FeedingLineStatus.FAULT,
    ],
)
def test_manual_control_can_be_acquired_only_when_line_is_available(feeding_line, status):
    feeding_line._status = status

    with pytest.raises(FeedingLineUnavailableException):
        feeding_line.acquire_manual_control(operator_id="operator")


def test_manual_control_can_be_acquired_when_line_is_available(feeding_line):
    feeding_line.acquire_manual_control(operator_id="operator")

    assert feeding_line.status == FeedingLineStatus.MANUAL_CONTROL
