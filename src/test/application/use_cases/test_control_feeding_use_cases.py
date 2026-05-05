import pytest

from application.use_cases.feeding.control_feeding_use_cases import (
    CancelFeedingUseCase,
    UpdateFeedingAmountUseCase,
)
from domain.dtos.machine_io import MachineVisitStatus
from domain.entities.cage_feeding import CageFeeding
from domain.entities.feeding_event import FeedingEventType
from domain.entities.feeding_session import FeedingSession, FeedingType, SessionStatus
from domain.value_objects import BlowerPowerPercentage, LineId


class _SessionRepo:
    def __init__(self, session):
        self.session = session
        self.saved = None

    async def find_by_id(self, session_id: str):
        return self.session if self.session.id == session_id else None

    async def save(self, session):
        self.saved = session


class _CageFeedingRepo:
    def __init__(self, cage_feedings=None):
        self.cage_feedings = cage_feedings or []
        self.saved = None

    async def find_by_session(self, session_id: str):
        return self.cage_feedings

    async def save(self, cage_feeding):
        self.saved = cage_feeding


class _EventRepo:
    def __init__(self):
        self.saved = []

    async def save(self, event):
        self.saved.append(event)


class _Line:
    def __init__(self):
        self.blower = _Blower()
        self.released = False

    def release_from_feeding(self):
        self.released = True


class _Blower:
    def __init__(self):
        self.current_power = BlowerPowerPercentage(80.0)


class _LineRepo:
    def __init__(self, line):
        self.line = line
        self.saved = None

    async def find_by_id(self, line_id: LineId):
        return self.line

    async def save(self, line):
        self.saved = line


class _Machine:
    def __init__(self):
        self.stopped_line_id = None
        self.target_amount = None
        self.status = MachineVisitStatus(
            is_running=True,
            is_paused=False,
            dispensed_kg=0.0,
            current_flow_rate_kg_per_min=1.0,
            has_error=False,
        )

    async def get_status(self, line_id: LineId):
        return self.status

    async def set_target_amount(self, line_id: LineId, target_kg: float):
        self.target_amount = target_kg

    async def stop(self, line_id: LineId):
        self.stopped_line_id = line_id


class _ActivityLogRepo:
    async def save(self, entry):
        pass


@pytest.mark.asyncio
async def test_cancel_feeding_stops_machine_and_turns_off_persisted_blower():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.MANUAL,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=10.0,
    )
    session.start()
    line = _Line()
    session_repo = _SessionRepo(session)
    line_repo = _LineRepo(line)
    machine = _Machine()

    use_case = CancelFeedingUseCase(
        session_repo=session_repo,
        cage_feeding_repo=_CageFeedingRepo(),
        event_repo=_EventRepo(),
        line_repo=line_repo,
        machine=machine,
        activity_log_repository=_ActivityLogRepo(),
    )

    await use_case.execute(session.id, operator_id="operator-2", reason="manual stop")

    assert machine.stopped_line_id == line_id
    assert line.blower.current_power.value == 0.0
    assert line.released is True
    assert line_repo.saved is line
    assert session_repo.saved.status == SessionStatus.CANCELLED


@pytest.mark.asyncio
async def test_update_feeding_amount_updates_active_cage_feeding_machine_and_session_total():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.MANUAL,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=10.0,
    )
    session.start()

    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=1,
        rate_kg_per_min=2.0,
    )
    cage_feeding.start()
    session_repo = _SessionRepo(session)
    cage_feeding_repo = _CageFeedingRepo([cage_feeding])
    event_repo = _EventRepo()
    machine = _Machine()
    machine.status = MachineVisitStatus(
        is_running=True,
        is_paused=False,
        dispensed_kg=3.0,
        current_flow_rate_kg_per_min=2.0,
        has_error=False,
    )

    use_case = UpdateFeedingAmountUseCase(
        session_repo=session_repo,
        cage_feeding_repo=cage_feeding_repo,
        event_repo=event_repo,
        machine=machine,
    )

    new_amount = await use_case.execute(session.id, new_amount_kg=12.5)

    assert new_amount == 12.5
    assert cage_feeding_repo.saved.programmed_kg == 12.5
    assert machine.target_amount == 12.5
    assert session_repo.saved.total_programmed_kg == 12.5
    assert event_repo.saved[0].event_type == FeedingEventType.AMOUNT_CHANGED
    assert event_repo.saved[0].data["previous_amount_kg"] == 10.0
    assert event_repo.saved[0].data["new_amount_kg"] == 12.5
    assert event_repo.saved[0].data["live_dispensed_kg"] == 3.0


@pytest.mark.asyncio
async def test_update_feeding_amount_rejects_amount_below_live_dispensed():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.MANUAL,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=10.0,
    )
    session.start()

    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=1,
        rate_kg_per_min=2.0,
    )
    cage_feeding.start()
    machine = _Machine()
    machine.status = MachineVisitStatus(
        is_running=True,
        is_paused=False,
        dispensed_kg=6.0,
        current_flow_rate_kg_per_min=2.0,
        has_error=False,
    )

    use_case = UpdateFeedingAmountUseCase(
        session_repo=_SessionRepo(session),
        cage_feeding_repo=_CageFeedingRepo([cage_feeding]),
        event_repo=_EventRepo(),
        machine=machine,
    )

    with pytest.raises(ValueError, match="no puede ser menor"):
        await use_case.execute(session.id, new_amount_kg=5.0)
