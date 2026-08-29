from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.models.feeding_models import ScheduledFeedingPlanRequest


def _payload(end_time="17:00"):
    return {
        "name": "Plan diurno",
        "line_id": str(uuid4()),
        "group_id": str(uuid4()),
        "doser_id": str(uuid4()),
        "silo_id": str(uuid4()),
        "start_time": "08:00",
        "end_time": end_time,
        "cage_configs": [{"cage_id": str(uuid4()), "mode": "FASTING", "daily_target_kg": 0}],
    }


@pytest.mark.parametrize("end_time", ["08:00", "07:59"])
def test_request_rejects_an_overnight_or_empty_window(end_time):
    with pytest.raises(ValidationError, match="mismo día"):
        ScheduledFeedingPlanRequest.model_validate(_payload(end_time))


@pytest.mark.parametrize("timezone", ["Mars/Olympus", "", "   "])
def test_request_rejects_invalid_timezones(timezone):
    payload = _payload()
    payload["timezone"] = timezone

    with pytest.raises(ValidationError, match="zona horaria"):
        ScheduledFeedingPlanRequest.model_validate(payload)


def test_request_normalizes_a_valid_timezone():
    payload = _payload()
    payload["timezone"] = " UTC "

    request = ScheduledFeedingPlanRequest.model_validate(payload)

    assert request.timezone == "UTC"
