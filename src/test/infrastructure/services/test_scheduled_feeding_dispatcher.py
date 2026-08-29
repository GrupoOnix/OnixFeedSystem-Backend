import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

import infrastructure.services.background_tasks as background_tasks_module
import infrastructure.services.scheduled_feeding_dispatcher as dispatcher_module
from infrastructure.services.scheduled_feeding_dispatcher import ScheduledFeedingDispatcher


TZ = ZoneInfo("America/Santiago")
NOW = datetime(2026, 8, 27, 10, 10, tzinfo=TZ)


class _Session:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False


class _FixedDateTime:
    @classmethod
    def now(cls, timezone):
        return NOW.astimezone(timezone)


@pytest.mark.asyncio
async def test_dispatcher_routes_due_and_expired_plans_once(monkeypatch):
    due = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        timezone="America/Santiago",
        start_time="10:00",
    )
    expired = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        timezone="America/Santiago",
        start_time="09:30",
    )
    future = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        timezone="America/Santiago",
        start_time="10:30",
    )
    inactive = SimpleNamespace(
        id=uuid4(),
        is_active=False,
        timezone="America/Santiago",
        start_time="10:00",
    )

    class _PlanRepository:
        def __init__(self, _db):
            pass

        async def list(self):
            return [due, expired, future, inactive]

    monkeypatch.setattr(dispatcher_module, "ScheduledFeedingPlanRepository", _PlanRepository)
    monkeypatch.setattr(dispatcher_module, "datetime", _FixedDateTime)

    dispatcher = ScheduledFeedingDispatcher(
        machine=object(),
        session_factory=lambda: _Session(),
        grace_period=timedelta(minutes=15),
    )
    dispatcher._claim_and_dispatch = AsyncMock()
    dispatcher._mark_missed = AsyncMock()

    await dispatcher.dispatch_due_plans()

    dispatcher._claim_and_dispatch.assert_awaited_once_with(due.id, NOW)
    dispatcher._mark_missed.assert_awaited_once()
    missed_plan_id, missed_now, expires_at = dispatcher._mark_missed.await_args.args
    assert missed_plan_id == expired.id
    assert missed_now == NOW
    assert expires_at == datetime(2026, 8, 27, 9, 45, tzinfo=TZ)


@pytest.mark.asyncio
async def test_scheduled_feeding_job_retries_after_error_and_propagates_cancellation(monkeypatch):
    dispatcher = SimpleNamespace(
        dispatch_due_plans=AsyncMock(
            side_effect=[RuntimeError("fallo transitorio"), asyncio.CancelledError()],
        )
    )
    sleep_intervals = []

    async def _sleep(seconds):
        sleep_intervals.append(seconds)

    monkeypatch.setattr(background_tasks_module.asyncio, "sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await background_tasks_module.scheduled_feeding_job(dispatcher, poll_interval_seconds=7)

    assert dispatcher.dispatch_due_plans.await_count == 2
    assert sleep_intervals == [7]
