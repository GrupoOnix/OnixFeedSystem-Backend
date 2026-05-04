import pytest

from application.use_cases.feeding.control_feeding_use_cases import CancelFeedingUseCase
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
    async def find_by_session(self, session_id: str):
        return []


class _EventRepo:
    def __init__(self):
        self.saved = []

    async def save(self, event):
        self.saved.append(event)


class _Line:
    def __init__(self):
        self.blower = _Blower()


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
    assert line_repo.saved is line
    assert session_repo.saved.status == SessionStatus.CANCELLED
