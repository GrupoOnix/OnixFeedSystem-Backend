import pytest

from domain.services.scheduled_feeding_time import (
    calculate_remaining_seconds,
    calculate_window_seconds,
)


def test_calculates_window_and_remaining_seconds_for_the_same_day():
    window = calculate_window_seconds("08:30", "17:00")

    assert window == 30_600
    assert calculate_remaining_seconds(window, 12_345.6789) == 18_254.321


@pytest.mark.parametrize("end_time", ["08:30", "07:59"])
def test_rejects_schedule_that_does_not_finish_the_same_day(end_time):
    with pytest.raises(ValueError, match="mismo día"):
        calculate_window_seconds("08:30", end_time)
