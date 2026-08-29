from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from infrastructure.services.scheduled_feeding_window import (
    ScheduledFeedingWindowStatus,
    evaluate_scheduled_feeding_window,
)


TZ = ZoneInfo("America/Santiago")
GRACE_PERIOD = timedelta(minutes=15)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 8, 27, 9, 59, 59, tzinfo=TZ), ScheduledFeedingWindowStatus.NOT_DUE),
        (datetime(2026, 8, 27, 10, 0, 0, tzinfo=TZ), ScheduledFeedingWindowStatus.DUE),
        (datetime(2026, 8, 27, 10, 14, 59, tzinfo=TZ), ScheduledFeedingWindowStatus.DUE),
        (datetime(2026, 8, 27, 10, 15, 0, tzinfo=TZ), ScheduledFeedingWindowStatus.EXPIRED),
    ],
)
def test_evaluate_scheduled_feeding_window_handles_its_boundaries(now, expected):
    window = evaluate_scheduled_feeding_window("10:00", now, GRACE_PERIOD)

    assert window.status == expected
    assert window.scheduled_at == datetime(2026, 8, 27, 10, 0, tzinfo=TZ)
    assert window.expires_at == datetime(2026, 8, 27, 10, 15, tzinfo=TZ)


def test_evaluate_scheduled_feeding_window_requires_an_aware_clock():
    with pytest.raises(ValueError, match="zona horaria"):
        evaluate_scheduled_feeding_window("10:00", datetime(2026, 8, 27, 10, 0), GRACE_PERIOD)
