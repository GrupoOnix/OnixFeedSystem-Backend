import pytest

from application.services import feeding_orchestrator
from application.services.feeding_orchestrator import FeedingOrchestrator
from domain.entities.cage_feeding import CageFeeding, CageFeedingMode
from domain.entities.feeding_session import SessionStatus
from domain.value_objects import BlowerPowerPercentage, LineId
from domain.value_objects.identifiers import SiloId


class _NoopSession:
    async def commit(self):
        pass

    async def rollback(self):
        pass


class _SessionFactory:
    def __call__(self):
        return self

    async def __aenter__(self):
        return _NoopSession()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _Line:
    def __init__(self):
        self.blower = _Blower()


class _Blower:
    def __init__(self):
        self.current_power = BlowerPowerPercentage(75.0)


class _Machine:
    async def stop(self, line_id):
        pass


@pytest.mark.asyncio
async def test_turn_off_persisted_blower_sets_current_power_to_zero(monkeypatch):
    line = _Line()
    saved_lines = []

    class _FeedingLineRepository:
        def __init__(self, db):
            self.db = db

        async def find_by_id(self, line_id):
            return line

        async def save(self, line_to_save):
            saved_lines.append(line_to_save)

    monkeypatch.setattr(
        feeding_orchestrator,
        "FeedingLineRepository",
        _FeedingLineRepository,
    )

    orchestrator = FeedingOrchestrator(
        machine=_Machine(),
        session_factory=_SessionFactory(),
    )

    await orchestrator._turn_off_persisted_blower(LineId.generate())

    assert line.blower.current_power.value == 0.0
    assert saved_lines == [line]


@pytest.mark.asyncio
async def test_cyclic_run_keeps_visiting_finished_cages_without_dispensing(monkeypatch):
    line_id = LineId.generate()
    silo_id = SiloId.generate()
    status = type("_Status", (), {"value": SessionStatus.IN_PROGRESS.value})()
    session = type(
        "_Session",
        (),
        {
            "id": "session-1",
            "status": status,
            "actual_start": None,
            "complete": lambda self: setattr(self.status, "value", SessionStatus.COMPLETED.value),
        },
    )()

    first = CageFeeding(
        feeding_session_id=session.id,
        cage_id="00000000-0000-0000-0000-000000000001",
        doser_id="00000000-0000-0000-0000-000000000101",
        silo_id=str(silo_id.value),
        execution_order=1,
        programmed_kg=10,
        programmed_visits=15,
        rate_kg_per_min=10,
        mode=CageFeedingMode.NORMAL,
    )
    second = CageFeeding(
        feeding_session_id=session.id,
        cage_id="00000000-0000-0000-0000-000000000002",
        doser_id="00000000-0000-0000-0000-000000000101",
        silo_id=str(silo_id.value),
        execution_order=2,
        programmed_kg=12,
        programmed_visits=10,
        rate_kg_per_min=10,
        mode=CageFeedingMode.NORMAL,
    )
    calls = []

    class _FeedingSessionRepository:
        def __init__(self, db):
            self.db = db

        async def find_by_id(self, session_id):
            return session

        async def save(self, session_to_save):
            pass

    class _FeedingEventRepository:
        def __init__(self, db):
            self.db = db

        async def save(self, event):
            pass

    class _CageFeedingRepository:
        def __init__(self, db):
            self.db = db

        async def find_by_id(self, cage_feeding_id):
            return next(
                cf for cf in (first, second)
                if cf.id == cage_feeding_id
            )

    async def _execute_visit(self, **kwargs):
        cage_feeding = kwargs["cage_feeding"]
        calls.append(("food", cage_feeding.cage_id, kwargs["visit_number"]))
        if cage_feeding.status.value == "PENDING":
            cage_feeding.start()
        cage_feeding.increment_completed_visits()
        if cage_feeding.completed_visits >= cage_feeding.programmed_visits:
            cage_feeding.complete()

    async def _execute_empty_visit(self, **kwargs):
        calls.append(("empty", kwargs["cage_feeding"].cage_id, kwargs["visit_number"]))

    async def _noop(self, line_id):
        pass

    monkeypatch.setattr(feeding_orchestrator, "FeedingSessionRepository", _FeedingSessionRepository)
    monkeypatch.setattr(feeding_orchestrator, "FeedingEventRepository", _FeedingEventRepository)
    monkeypatch.setattr(feeding_orchestrator, "CageFeedingRepository", _CageFeedingRepository)
    monkeypatch.setattr(FeedingOrchestrator, "_execute_visit", _execute_visit)
    monkeypatch.setattr(FeedingOrchestrator, "_execute_empty_visit", _execute_empty_visit)
    monkeypatch.setattr(FeedingOrchestrator, "_turn_off_persisted_blower", _noop)
    monkeypatch.setattr(FeedingOrchestrator, "_release_feeding_line", _noop)

    orchestrator = FeedingOrchestrator(
        machine=_Machine(),
        session_factory=_SessionFactory(),
        poll_interval_seconds=0,
    )

    await orchestrator.run(
        session=session,
        cage_feedings=[first, second],
        line_id=line_id,
        slot_map={first.cage_id: 1, second.cage_id: 2},
        silo_id=silo_id,
        blower_power_percentage=70,
        transport_time_map={first.cage_id: 1, second.cage_id: 1},
    )

    assert len(calls) == 30
    assert calls.count(("food", first.cage_id, 15)) == 1
    assert calls.count(("food", second.cage_id, 10)) == 1
    assert [
        call
        for call in calls
        if call[0] == "empty" and call[1] == second.cage_id
    ] == [
        ("empty", second.cage_id, 11),
        ("empty", second.cage_id, 12),
        ("empty", second.cage_id, 13),
        ("empty", second.cage_id, 14),
        ("empty", second.cage_id, 15),
    ]
