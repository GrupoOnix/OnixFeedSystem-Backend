import pytest

from application.services import feeding_orchestrator
from application.services.feeding_orchestrator import FeedingOrchestrator
from domain.dtos.machine_io import MachineVisitStatus, VisitStage
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


def _clone_cage_feeding(cage_feeding):
    clone = CageFeeding(
        feeding_session_id=cage_feeding.feeding_session_id,
        cage_id=cage_feeding.cage_id,
        doser_id=cage_feeding.doser_id,
        silo_id=cage_feeding.silo_id,
        execution_order=cage_feeding.execution_order,
        programmed_kg=cage_feeding.programmed_kg,
        programmed_visits=cage_feeding.programmed_visits,
        rate_kg_per_min=cage_feeding.rate_kg_per_min,
        mode=cage_feeding.mode,
    )
    clone._id = cage_feeding.id
    clone._status = cage_feeding.status
    clone._completed_visits = cage_feeding.completed_visits
    clone._dispensed_kg = cage_feeding.dispensed_kg
    return clone


@pytest.mark.asyncio
async def test_execute_visit_uses_refreshed_programmed_kg_from_repository(monkeypatch):
    line_id = LineId.generate()
    silo_id = SiloId.generate()
    session = type(
        "_Session",
        (),
        {
            "id": "session-1",
            "status": type("_Status", (), {"value": SessionStatus.IN_PROGRESS.value})(),
        },
    )()
    stale = CageFeeding(
        feeding_session_id=session.id,
        cage_id="00000000-0000-0000-0000-000000000001",
        doser_id="00000000-0000-0000-0000-000000000101",
        silo_id=str(silo_id.value),
        execution_order=1,
        programmed_kg=10,
        programmed_visits=2,
        rate_kg_per_min=3,
        mode=CageFeedingMode.NORMAL,
    )
    refreshed = _clone_cage_feeding(stale)
    refreshed.set_programmed_kg(14)
    commands = []

    class _MachineWithStatus:
        async def start_visit(self, line_id, command):
            commands.append(command)

        async def get_status(self, line_id):
            return MachineVisitStatus(
                is_running=False,
                is_paused=False,
                dispensed_kg=14,
                current_flow_rate_kg_per_min=0,
                has_error=False,
                current_stage=VisitStage.COMPLETED,
            )

    class _CageFeedingRepository:
        def __init__(self, db):
            self.db = db

        async def find_by_id(self, cage_feeding_id):
            return refreshed

        async def save(self, cage_feeding):
            pass

    class _FeedingSessionRepository:
        def __init__(self, db):
            self.db = db

        async def find_by_id(self, session_id):
            return session

    class _FeedingEventRepository:
        def __init__(self, db):
            self.db = db

        async def save(self, event):
            pass

    class _SiloRepository:
        def __init__(self, db):
            self.db = db

        async def find_by_id(self, silo_id):
            return None

    monkeypatch.setattr(feeding_orchestrator, "CageFeedingRepository", _CageFeedingRepository)
    monkeypatch.setattr(feeding_orchestrator, "FeedingSessionRepository", _FeedingSessionRepository)
    monkeypatch.setattr(feeding_orchestrator, "FeedingEventRepository", _FeedingEventRepository)
    monkeypatch.setattr(feeding_orchestrator, "SiloRepository", _SiloRepository)

    orchestrator = FeedingOrchestrator(
        machine=_MachineWithStatus(),
        session_factory=_SessionFactory(),
        poll_interval_seconds=0,
    )

    await orchestrator._execute_visit(
        session=session,
        cage_feeding=stale,
        line_id=line_id,
        slot_number=1,
        silo_id=silo_id,
        blower_power_percentage=70,
        visit_number=1,
    )

    assert commands[0].target_kg == 14


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


@pytest.mark.asyncio
async def test_cyclic_run_applies_blow_before_once_and_blow_after_once_after_refresh(monkeypatch):
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
        programmed_visits=2,
        rate_kg_per_min=10,
        mode=CageFeedingMode.NORMAL,
    )
    second = CageFeeding(
        feeding_session_id=session.id,
        cage_id="00000000-0000-0000-0000-000000000002",
        doser_id="00000000-0000-0000-0000-000000000101",
        silo_id=str(silo_id.value),
        execution_order=2,
        programmed_kg=10,
        programmed_visits=2,
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
            original = next(
                cf for cf in (first, second)
                if cf.id == cage_feeding_id
            )
            return _clone_cage_feeding(original)

    async def _execute_visit(self, **kwargs):
        calls.append(
            (
                kwargs["cage_feeding"].cage_id,
                kwargs["visit_number"],
                kwargs["blow_before_seconds"],
                kwargs["blow_after_seconds"],
            )
        )

    async def _noop(self, line_id):
        pass

    monkeypatch.setattr(feeding_orchestrator, "FeedingSessionRepository", _FeedingSessionRepository)
    monkeypatch.setattr(feeding_orchestrator, "FeedingEventRepository", _FeedingEventRepository)
    monkeypatch.setattr(feeding_orchestrator, "CageFeedingRepository", _CageFeedingRepository)
    monkeypatch.setattr(FeedingOrchestrator, "_execute_visit", _execute_visit)
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
        blow_before_seconds=11,
        blow_after_seconds=13,
    )

    assert [call[2] for call in calls] == [11, 0.0, 0.0, 0.0]
    assert [call[3] for call in calls] == [0.0, 0.0, 0.0, 13]


@pytest.mark.asyncio
async def test_cyclic_run_waits_after_intermediate_visits_only(monkeypatch):
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

    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="00000000-0000-0000-0000-000000000001",
        doser_id="00000000-0000-0000-0000-000000000101",
        silo_id=str(silo_id.value),
        execution_order=1,
        programmed_kg=10,
        programmed_visits=3,
        rate_kg_per_min=10,
        mode=CageFeedingMode.NORMAL,
    )
    visits = []
    sleeps = []

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
            return cage_feeding

    async def _execute_visit(self, **kwargs):
        visits.append(kwargs["visit_number"])
        if cage_feeding.status.value == "PENDING":
            cage_feeding.start()
        cage_feeding.increment_completed_visits()
        if cage_feeding.completed_visits >= cage_feeding.programmed_visits:
            cage_feeding.complete()

    async def _sleep(seconds):
        sleeps.append(seconds)

    async def _noop(self, line_id):
        pass

    monkeypatch.setattr(feeding_orchestrator, "FeedingSessionRepository", _FeedingSessionRepository)
    monkeypatch.setattr(feeding_orchestrator, "FeedingEventRepository", _FeedingEventRepository)
    monkeypatch.setattr(feeding_orchestrator, "CageFeedingRepository", _CageFeedingRepository)
    monkeypatch.setattr(feeding_orchestrator.asyncio, "sleep", _sleep)
    monkeypatch.setattr(FeedingOrchestrator, "_execute_visit", _execute_visit)
    monkeypatch.setattr(FeedingOrchestrator, "_turn_off_persisted_blower", _noop)
    monkeypatch.setattr(FeedingOrchestrator, "_release_feeding_line", _noop)

    orchestrator = FeedingOrchestrator(
        machine=_Machine(),
        session_factory=_SessionFactory(),
        poll_interval_seconds=0,
    )

    await orchestrator.run(
        session=session,
        cage_feedings=[cage_feeding],
        line_id=line_id,
        slot_map={cage_feeding.cage_id: 1},
        silo_id=silo_id,
        blower_power_percentage=70,
        transport_time_map={cage_feeding.cage_id: 1},
        wait_after_visit_seconds=9,
    )

    assert visits == [1, 2, 3]
    assert sleeps == [9, 9]

@pytest.fixture(autouse=True)
def _mock_inventory_repository(monkeypatch):
    class _InventoryRepository:
        def __init__(self, db):
            self.db = db

        async def consume(self, *args, **kwargs):
            return None

        async def release(self, *args, **kwargs):
            return None

    monkeypatch.setattr(
        feeding_orchestrator,
        "SiloInventoryRepository",
        _InventoryRepository,
    )
