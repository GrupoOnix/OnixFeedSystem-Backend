from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from infrastructure.persistence.models.scheduled_feeding_run_model import ScheduledFeedingRunModel
from infrastructure.persistence.repositories.scheduled_feeding_run_repository import ScheduledFeedingRunRepository


class _Result:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        return self

    def first(self):
        return self._value


class _Session:
    def __init__(self, results):
        self._results = iter(results)
        self.flushes = 0

    async def execute(self, _statement):
        return _Result(next(self._results))

    async def flush(self):
        self.flushes += 1


@pytest.mark.asyncio
async def test_claim_returns_inserted_run_to_single_winner():
    run = ScheduledFeedingRunModel(plan_id=uuid4(), run_date=date.today())
    repository = ScheduledFeedingRunRepository(_Session([run]))

    claimed = await repository.claim(run.plan_id, run.run_date, "worker-a", lease_seconds=60)

    assert claimed is run


@pytest.mark.asyncio
async def test_claim_reclaims_only_an_expired_claim():
    run = ScheduledFeedingRunModel(
        plan_id=uuid4(),
        run_date=date.today(),
        worker_id="worker-lost",
        lease_expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    session = _Session([None, run])
    repository = ScheduledFeedingRunRepository(session)

    claimed = await repository.claim(run.plan_id, run.run_date, "worker-new", lease_seconds=60)

    assert claimed is run
    assert run.worker_id == "worker-new"
    assert run.attempts == 2
    assert run.lease_expires_at > datetime.now(timezone.utc)
    assert session.flushes == 1


@pytest.mark.asyncio
async def test_claim_does_not_reuse_an_enqueued_run():
    run = ScheduledFeedingRunModel(
        plan_id=uuid4(),
        run_date=date.today(),
        status="ENQUEUED",
        lease_expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    repository = ScheduledFeedingRunRepository(_Session([None, run]))

    claimed = await repository.claim(run.plan_id, run.run_date, "worker-new", lease_seconds=60)

    assert claimed is None


@pytest.mark.asyncio
async def test_mark_missed_creates_a_terminal_run_once():
    run = ScheduledFeedingRunModel(plan_id=uuid4(), run_date=date.today(), status="MISSED", attempts=0)
    repository = ScheduledFeedingRunRepository(_Session([run]))

    recorded = await repository.mark_missed(run.plan_id, run.run_date, "Ventana vencida")

    assert recorded is run
    assert recorded.status == "MISSED"
