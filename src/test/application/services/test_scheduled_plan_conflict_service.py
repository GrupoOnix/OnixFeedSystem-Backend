from types import SimpleNamespace

import pytest

from application.services.scheduled_plan_conflict_service import (
    ScheduledPlanConflictError,
    assert_no_scheduled_plan_conflict,
)


def _plan(name, start_time, end_time, timezone="America/Santiago"):
    return SimpleNamespace(name=name, start_time=start_time, end_time=end_time, timezone=timezone)


def test_allows_contiguous_active_plans_on_the_same_line():
    assert_no_scheduled_plan_conflict(
        start_time="10:00",
        end_time="12:00",
        timezone="America/Santiago",
        existing_plans=[_plan("Mañana", "08:00", "10:00")],
    )


def test_rejects_overlapping_active_plans_on_the_same_line():
    with pytest.raises(ScheduledPlanConflictError, match="superpone"):
        assert_no_scheduled_plan_conflict(
            start_time="09:00",
            end_time="11:00",
            timezone="America/Santiago",
            existing_plans=[_plan("Mañana", "08:00", "10:00")],
        )


def test_rejects_mixed_timezones_for_active_plans_on_the_same_line():
    with pytest.raises(ScheduledPlanConflictError, match="zona horaria"):
        assert_no_scheduled_plan_conflict(
            start_time="10:00",
            end_time="12:00",
            timezone="UTC",
            existing_plans=[_plan("Mañana", "08:00", "10:00")],
        )
