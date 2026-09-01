import asyncio
from types import SimpleNamespace

import pytest

from domain.dtos.machine_io import MachineVisitStatus, VisitStage
from domain.entities.cage_feeding import CageFeeding, CageFeedingMode
from domain.entities.feeding_session import FeedingSession, FeedingType, SessionStatus
from infrastructure.services.feeding_execution_worker import FeedingExecutionWorker


class _AsyncSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def commit(self):
        return None


class _Machine:
    def __init__(self):
        self.stopped = False

    async def get_status(self, _line_id):
        return MachineVisitStatus(
            is_running=False,
            is_paused=False,
            dispensed_kg=0.0,
            current_flow_rate_kg_per_min=0.0,
            has_error=False,
            current_stage=VisitStage.IDLE,
        )

    async def stop(self, _line_id):
        self.stopped = True


@pytest.mark.asyncio
async def test_recovery_stops_machine_interrupts_session_and_releases_resources(monkeypatch):
    machine = _Machine()
    session = FeedingSession(
        feeding_type=FeedingType.MANUAL,
        line_id="00000000-0000-0000-0000-000000000001",
        operator_id="operator",
        total_programmed_kg=10,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="00000000-0000-0000-0000-000000000002",
        doser_id="00000000-0000-0000-0000-000000000003",
        silo_id="00000000-0000-0000-0000-000000000004",
        execution_order=1,
        programmed_kg=10,
        programmed_visits=1,
        rate_kg_per_min=10,
        mode=CageFeedingMode.NORMAL,
    )
    released = SimpleNamespace(line=False, inventory=False, job_reason=None)

    class _SessionRepo:
        def __init__(self, _db):
            pass

        async def find_by_id(self, _id):
            return session

        async def save(self, _session):
            return None

    class _CageRepo:
        def __init__(self, _db):
            pass

        async def find_by_session(self, _id):
            return [cage_feeding]

    class _EventRepo:
        def __init__(self, _db):
            pass

        async def save(self, _event):
            return None

    class _InventoryRepo:
        def __init__(self, _db):
            pass

        async def release(self, _id):
            released.inventory = True

    class _Line:
        def release_from_feeding(self):
            released.line = True

    class _LineRepo:
        def __init__(self, _db):
            pass

        async def find_by_id(self, _id):
            return _Line()

        async def save(self, _line):
            return None

    class _JobRepo:
        def __init__(self, _db):
            pass

        async def mark_interrupted(self, _id, reason):
            released.job_reason = reason

    import infrastructure.services.feeding_execution_worker as worker_module

    monkeypatch.setattr(worker_module, "FeedingSessionRepository", _SessionRepo)
    monkeypatch.setattr(worker_module, "CageFeedingRepository", _CageRepo)
    monkeypatch.setattr(worker_module, "FeedingEventRepository", _EventRepo)
    monkeypatch.setattr(worker_module, "SiloInventoryRepository", _InventoryRepo)
    monkeypatch.setattr(worker_module, "FeedingLineRepository", _LineRepo)
    monkeypatch.setattr(worker_module, "FeedingExecutionJobRepository", _JobRepo)

    worker = FeedingExecutionWorker(machine, lambda: _AsyncSession())
    job = SimpleNamespace(
        id="job-1",
        feeding_session_id=session.id,
        payload={"line_id": session.line_id},
    )

    assert await worker._interrupt_job(job, "Proceso reiniciado") is True
    assert machine.stopped is True
    assert session.status == SessionStatus.INTERRUPTED
    assert released.line is True
    assert released.inventory is True
    assert released.job_reason == "Proceso reiniciado"


@pytest.mark.asyncio
async def test_worker_starts_second_job_without_waiting_for_first_to_finish(monkeypatch):
    """Las alimentaciones de líneas distintas no deben quedar serializadas."""
    worker = FeedingExecutionWorker(_Machine(), lambda: _AsyncSession(), poll_interval_seconds=0.01)
    jobs = iter([SimpleNamespace(id="job-1"), SimpleNamespace(id="job-2"), None])
    both_started = asyncio.Event()
    release_jobs = asyncio.Event()
    started: list[str] = []

    async def recover_one_expired_job():
        return False

    async def claim_next_job():
        return next(jobs)

    async def execute(job):
        started.append(job.id)
        if len(started) == 2:
            both_started.set()
        await release_jobs.wait()

    monkeypatch.setattr(worker, "_recover_one_expired_job", recover_one_expired_job)
    monkeypatch.setattr(worker, "_claim_next_job", claim_next_job)
    monkeypatch.setattr(worker, "_execute", execute)

    run_task = asyncio.create_task(worker.run())
    try:
        await asyncio.wait_for(both_started.wait(), timeout=0.5)
        assert started == ["job-1", "job-2"]
    finally:
        release_jobs.set()
        run_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await run_task
