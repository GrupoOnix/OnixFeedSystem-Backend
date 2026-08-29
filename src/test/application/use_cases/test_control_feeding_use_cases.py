import pytest

from application.use_cases.feeding.control_feeding_use_cases import (
    CancelFeedingUseCase,
    UpdateCageModeUseCase,
    UpdateCyclicCageAmountUseCase,
    UpdateCyclicCageRateUseCase,
    UpdateFeedingAmountUseCase,
)
from domain.dtos.machine_io import MachineVisitStatus
from domain.entities.cage_feeding import CageFeeding, CageFeedingMode
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

    async def update_rate(self, cage_feeding_id, rate_kg_per_min):
        cage_feeding = next(cf for cf in self.cage_feedings if cf.id == cage_feeding_id)
        cage_feeding.set_rate(rate_kg_per_min)
        self.saved = cage_feeding
        return cage_feeding

    async def update_programmed_kg(self, cage_feeding_id, programmed_kg):
        cage_feeding = next(cf for cf in self.cage_feedings if cf.id == cage_feeding_id)
        cage_feeding.set_programmed_kg(programmed_kg)
        self.saved = cage_feeding
        return cage_feeding

    async def update_amount_plan(self, cage_feeding_id, programmed_kg, visit_quantities_kg):
        cage_feeding = next(cf for cf in self.cage_feedings if cf.id == cage_feeding_id)
        cage_feeding.set_amount_plan(programmed_kg, visit_quantities_kg)
        self.saved = cage_feeding
        return cage_feeding

    async def update_mode(self, cage_feeding_id, mode):
        cage_feeding = next(cf for cf in self.cage_feedings if cf.id == cage_feeding_id)
        cage_feeding.set_mode(mode)
        self.saved = cage_feeding
        return cage_feeding

    async def record_visit_progress(self, cage_feeding_id, dispensed_kg, completed_visit):
        cage_feeding = next(cf for cf in self.cage_feedings if cf.id == cage_feeding_id)
        cage_feeding.add_dispensed_amount(dispensed_kg)
        if completed_visit:
            cage_feeding.increment_completed_visits()
        self.saved = cage_feeding
        return cage_feeding


class _EventRepo:
    def __init__(self):
        self.saved = []

    async def save(self, event):
        self.saved.append(event)


class _Line:
    def __init__(self, max_rate_kg_per_min=10.0):
        self.blower = _Blower()
        self.released = False
        self.doser = type("_Doser", (), {"max_rate_kg_per_min": max_rate_kg_per_min})()

    def release_from_feeding(self):
        self.released = True

    def get_doser_by_id(self, doser_id):
        return self.doser


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
        self.doser_rate = None
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

    async def set_doser_rate(self, line_id: LineId, rate_kg_per_min: float):
        self.doser_rate = rate_kg_per_min

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

    await use_case.execute(session.id, operator_id="operator-2", actor="operator-2", reason="manual stop")

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


@pytest.mark.asyncio
async def test_update_cage_mode_persists_pause_for_next_visit_without_touching_machine():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=150.0,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=15,
        rate_kg_per_min=2.0,
    )
    cage_feeding.start()
    cage_feeding.increment_completed_visits()
    cage_feeding_repo = _CageFeedingRepo([cage_feeding])
    event_repo = _EventRepo()

    use_case = UpdateCageModeUseCase(
        session_repo=_SessionRepo(session),
        cage_feeding_repo=cage_feeding_repo,
        event_repo=event_repo,
    )

    previous_mode, new_mode = await use_case.execute(
        session_id=session.id,
        cage_id=cage_feeding.cage_id,
        new_mode="PAUSE",
        operator_id="123e4567-e89b-12d3-a456-426614174099",
    )

    assert previous_mode == "NORMAL"
    assert new_mode == "PAUSE"
    assert cage_feeding_repo.saved.mode == CageFeedingMode.PAUSE
    assert event_repo.saved[0].event_type == FeedingEventType.CAGE_MODE_CHANGED
    assert event_repo.saved[0].data["applied_immediately"] is False


@pytest.mark.asyncio
async def test_update_cyclic_cage_amount_active_repartitions_remaining_visits_and_updates_machine():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=40.0,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=4,
        rate_kg_per_min=2.0,
    )
    cage_feeding.start()
    cage_feeding.increment_completed_visits()
    cage_feeding.add_dispensed_amount(10.0)
    machine = _Machine()
    machine.status = MachineVisitStatus(
        is_running=True,
        is_paused=False,
        dispensed_kg=2.0,
        current_flow_rate_kg_per_min=2.0,
        has_error=False,
        cage_id=cage_feeding.cage_id,
        cage_feeding_id=cage_feeding.id,
    )
    session_repo = _SessionRepo(session)
    cage_feeding_repo = _CageFeedingRepo([cage_feeding])
    event_repo = _EventRepo()
    use_case = UpdateCyclicCageAmountUseCase(
        session_repo=session_repo,
        cage_feeding_repo=cage_feeding_repo,
        event_repo=event_repo,
        machine=machine,
    )

    update = await use_case.execute(session.id, cage_feeding.cage_id, 52.0)

    assert update.total_amount_kg == 52.0
    assert cage_feeding_repo.saved.programmed_kg == pytest.approx(40.0 / 3)
    assert machine.target_amount == pytest.approx(46.0 / 3)
    assert cage_feeding_repo.saved.visit_quantities_kg == pytest.approx([10.0, 46.0 / 3, 40.0 / 3, 40.0 / 3])
    assert session_repo.saved.total_programmed_kg == pytest.approx(52.0)
    assert event_repo.saved[0].event_type == FeedingEventType.AMOUNT_CHANGED
    assert event_repo.saved[0].data["applied_immediately"] is True
    assert event_repo.saved[0].data["live_dispensed_kg"] == 2.0


@pytest.mark.asyncio
async def test_update_cyclic_cage_amount_pending_repartitions_without_touching_machine():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=40.0,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=4,
        rate_kg_per_min=2.0,
    )
    machine = _Machine()
    session_repo = _SessionRepo(session)
    cage_feeding_repo = _CageFeedingRepo([cage_feeding])
    event_repo = _EventRepo()
    use_case = UpdateCyclicCageAmountUseCase(
        session_repo=session_repo,
        cage_feeding_repo=cage_feeding_repo,
        event_repo=event_repo,
        machine=machine,
    )

    update = await use_case.execute(session.id, cage_feeding.cage_id, 60.0)

    assert cage_feeding_repo.saved.programmed_kg == 15.0
    assert cage_feeding_repo.saved.visit_quantities_kg == [15.0, 15.0, 15.0, 15.0]
    assert update.remaining_visit_quantities_kg == [15.0, 15.0, 15.0, 15.0]
    assert machine.target_amount is None
    assert session_repo.saved.total_programmed_kg == 60.0
    assert event_repo.saved[0].data["applied_immediately"] is False


@pytest.mark.asyncio
async def test_update_cyclic_cage_amount_allows_empty_remaining_visits():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=40.0,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=4,
        rate_kg_per_min=2.0,
        visit_quantities_kg=[10.0, 10.0, 10.0, 10.0],
    )
    cage_feeding.start()
    cage_feeding.increment_completed_visits()
    cage_feeding.add_dispensed_amount(10.0)
    cage_feeding_repo = _CageFeedingRepo([cage_feeding])
    use_case = UpdateCyclicCageAmountUseCase(
        session_repo=_SessionRepo(session),
        cage_feeding_repo=cage_feeding_repo,
        event_repo=_EventRepo(),
        machine=_Machine(),
    )

    update = await use_case.execute(session.id, cage_feeding.cage_id, 10.0)

    assert cage_feeding_repo.saved.programmed_kg == 0.0
    assert cage_feeding_repo.saved.visit_quantities_kg == [10.0, 0.0, 0.0, 0.0]
    assert update.remaining_visit_quantities_kg == [0.0, 0.0, 0.0]


@pytest.mark.asyncio
async def test_update_cyclic_cage_amount_rejects_total_below_already_dispensed():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=40.0,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=4,
        rate_kg_per_min=2.0,
    )
    cage_feeding.start()
    cage_feeding.increment_completed_visits()
    cage_feeding.add_dispensed_amount(10.0)
    machine = _Machine()
    machine.status = MachineVisitStatus(
        is_running=True,
        is_paused=False,
        dispensed_kg=5.0,
        current_flow_rate_kg_per_min=2.0,
        has_error=False,
        cage_id=cage_feeding.cage_id,
        cage_feeding_id=cage_feeding.id,
    )
    use_case = UpdateCyclicCageAmountUseCase(
        session_repo=_SessionRepo(session),
        cage_feeding_repo=_CageFeedingRepo([cage_feeding]),
        event_repo=_EventRepo(),
        machine=machine,
    )

    with pytest.raises(ValueError, match="no puede ser menor"):
        await use_case.execute(session.id, cage_feeding.cage_id, 14.0)


@pytest.mark.asyncio
async def test_update_cyclic_cage_amount_rejects_fasting_cage():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=40.0,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=0.0,
        programmed_visits=0,
        rate_kg_per_min=0.0,
        mode=CageFeedingMode.FASTING,
    )
    use_case = UpdateCyclicCageAmountUseCase(
        session_repo=_SessionRepo(session),
        cage_feeding_repo=_CageFeedingRepo([cage_feeding]),
        event_repo=_EventRepo(),
        machine=_Machine(),
    )

    with pytest.raises(ValueError, match="FASTING"):
        await use_case.execute(session.id, cage_feeding.cage_id, 10.0)


@pytest.mark.asyncio
async def test_update_cyclic_cage_amount_rejects_non_cyclic_session():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.MANUAL,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=40.0,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=4,
        rate_kg_per_min=2.0,
    )
    use_case = UpdateCyclicCageAmountUseCase(
        session_repo=_SessionRepo(session),
        cage_feeding_repo=_CageFeedingRepo([cage_feeding]),
        event_repo=_EventRepo(),
        machine=_Machine(),
    )

    with pytest.raises(ValueError, match="solo aplica a sesiones cíclicas"):
        await use_case.execute(session.id, cage_feeding.cage_id, 10.0)


@pytest.mark.asyncio
async def test_update_cyclic_cage_amount_rejects_completed_cage():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=40.0,
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
    cage_feeding.increment_completed_visits()
    cage_feeding.complete()
    use_case = UpdateCyclicCageAmountUseCase(
        session_repo=_SessionRepo(session),
        cage_feeding_repo=_CageFeedingRepo([cage_feeding]),
        event_repo=_EventRepo(),
        machine=_Machine(),
    )

    with pytest.raises(ValueError, match="COMPLETED"):
        await use_case.execute(session.id, cage_feeding.cage_id, 10.0)


@pytest.mark.asyncio
async def test_update_cyclic_cage_rate_active_updates_machine_and_event():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=40.0,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=4,
        rate_kg_per_min=2.0,
    )
    cage_feeding.start()
    machine = _Machine()
    machine.status = MachineVisitStatus(
        is_running=True,
        is_paused=False,
        dispensed_kg=1.0,
        current_flow_rate_kg_per_min=2.0,
        has_error=False,
        cage_id=cage_feeding.cage_id,
        cage_feeding_id=cage_feeding.id,
    )
    event_repo = _EventRepo()
    use_case = UpdateCyclicCageRateUseCase(
        session_repo=_SessionRepo(session),
        cage_feeding_repo=_CageFeedingRepo([cage_feeding]),
        event_repo=event_repo,
        machine=machine,
        line_repo=_LineRepo(_Line(max_rate_kg_per_min=8.0)),
    )

    new_rate = await use_case.execute(session.id, cage_feeding.cage_id, 4.5)

    assert new_rate == 4.5
    assert machine.doser_rate == 4.5
    assert event_repo.saved[0].event_type == FeedingEventType.RATE_CHANGED
    assert event_repo.saved[0].data["applied_immediately"] is True


@pytest.mark.asyncio
async def test_update_cyclic_cage_rate_pending_persists_without_machine_update():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=40.0,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=4,
        rate_kg_per_min=2.0,
    )
    machine = _Machine()
    cage_feeding_repo = _CageFeedingRepo([cage_feeding])
    event_repo = _EventRepo()
    use_case = UpdateCyclicCageRateUseCase(
        session_repo=_SessionRepo(session),
        cage_feeding_repo=cage_feeding_repo,
        event_repo=event_repo,
        machine=machine,
        line_repo=_LineRepo(_Line(max_rate_kg_per_min=8.0)),
    )

    await use_case.execute(session.id, cage_feeding.cage_id, 4.5)

    assert cage_feeding_repo.saved.rate_kg_per_min == 4.5
    assert machine.doser_rate is None
    assert event_repo.saved[0].data["applied_immediately"] is False


@pytest.mark.asyncio
async def test_update_cyclic_cage_rate_rejects_doser_capacity():
    line_id = LineId.generate()
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(line_id),
        operator_id="operator-1",
        total_programmed_kg=40.0,
    )
    session.start()
    cage_feeding = CageFeeding(
        feeding_session_id=session.id,
        cage_id="123e4567-e89b-12d3-a456-426614174001",
        doser_id="123e4567-e89b-12d3-a456-426614174002",
        silo_id="123e4567-e89b-12d3-a456-426614174003",
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=4,
        rate_kg_per_min=2.0,
    )
    use_case = UpdateCyclicCageRateUseCase(
        session_repo=_SessionRepo(session),
        cage_feeding_repo=_CageFeedingRepo([cage_feeding]),
        event_repo=_EventRepo(),
        machine=_Machine(),
        line_repo=_LineRepo(_Line(max_rate_kg_per_min=3.0)),
    )

    with pytest.raises(ValueError, match="supera la capacidad"):
        await use_case.execute(session.id, cage_feeding.cage_id, 4.5)
