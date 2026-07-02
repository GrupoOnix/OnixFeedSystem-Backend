import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")
os.environ.setdefault("DB_NAME", "test")

from api.models.feeding_models import UpdateAmountRequest, UpdateCageModeRequest, UpdateRateRequest
from api.routers.feeding_router import (
    get_cage_visit_history,
    get_cyclic_feeding_status,
    get_session_history_detail,
    update_cage_mode,
    update_cyclic_cage_amount,
    update_cyclic_cage_rate,
)
from domain.dtos.machine_io import MachineVisitStatus, VisitStage
from domain.entities.cage_feeding import CageFeeding, CageFeedingMode
from domain.entities.feeding_event import FeedingEvent, FeedingEventType
from domain.entities.feeding_session import FeedingSession, FeedingType


class FakeCurrentUser:
    id = "123e4567-e89b-12d3-a456-426614174000"
    full_name = "Test User"
    username = "testuser"


class _UpdateCageModeUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, session_id, cage_id, new_mode, operator_id):
        self.calls.append((session_id, cage_id, new_mode, operator_id))
        return "NORMAL", new_mode


class _UpdateCyclicCageAmountUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, session_id, cage_id, new_amount):
        self.calls.append((session_id, cage_id, new_amount))
        return new_amount


class _UpdateCyclicCageRateUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, session_id, cage_id, new_rate):
        self.calls.append((session_id, cage_id, new_rate))
        return new_rate


class _FailingUseCase:
    async def execute(self, *args):
        raise ValueError("bad request")


class _SessionRepo:
    def __init__(self, session):
        self.session = session

    async def find_by_id(self, session_id):
        return self.session if self.session.id == session_id else None


class _CageFeedingRepo:
    def __init__(self, cage_feedings):
        self.cage_feedings = cage_feedings

    async def find_by_session(self, session_id):
        return self.cage_feedings


class _EventRepo:
    def __init__(self, events):
        self.events = events

    async def find_by_session(self, session_id):
        return [event for event in self.events if event.feeding_session_id == session_id]

    async def find_by_type(self, session_id, event_type):
        return [
            event for event in self.events if event.feeding_session_id == session_id and event.event_type == event_type
        ]


class _CageRepo:
    async def find_by_id(self, cage_id):
        return SimpleNamespace(name=SimpleNamespace(value=f"Cage {str(cage_id)[-4:]}"))


class _LineRepo:
    async def find_by_id(self, line_id):
        return SimpleNamespace(
            name=SimpleNamespace(value="Line A"),
            dosers=[],
        )


class _Machine:
    async def get_status(self, line_id):
        return MachineVisitStatus(
            is_running=True,
            is_paused=False,
            dispensed_kg=1.25,
            current_flow_rate_kg_per_min=3.0,
            has_error=False,
            current_stage=VisitStage.FEEDING,
        )


class _UserRepo:
    async def find_by_id(self, user_id):
        return SimpleNamespace(full_name="Test User")


def _cyclic_session_with_cages():
    session = FeedingSession(
        feeding_type=FeedingType.CYCLIC,
        line_id=str(uuid4()),
        operator_id=str(uuid4()),
        total_programmed_kg=220.0,
    )
    session.start()
    first = CageFeeding(
        feeding_session_id=session.id,
        cage_id=str(uuid4()),
        doser_id=str(uuid4()),
        silo_id=str(uuid4()),
        execution_order=1,
        programmed_kg=10.0,
        programmed_visits=15,
        rate_kg_per_min=2.0,
        mode=CageFeedingMode.NORMAL,
    )
    second = CageFeeding(
        feeding_session_id=session.id,
        cage_id=str(uuid4()),
        doser_id=str(uuid4()),
        silo_id=str(uuid4()),
        execution_order=2,
        programmed_kg=7.0,
        programmed_visits=10,
        rate_kg_per_min=2.0,
        mode=CageFeedingMode.PAUSE,
    )
    first.start()
    first.increment_completed_visits()
    first.add_dispensed_amount(10.0)
    session.add_cage_feeding(first)
    session.add_cage_feeding(second)
    return session, first, second


@pytest.mark.asyncio
async def test_patch_cage_mode_response_contract_marks_next_visits_only():
    session_id = str(uuid4())
    cage_id = str(uuid4())
    operator_id = str(uuid4())
    use_case = _UpdateCageModeUseCase()

    response = await update_cage_mode(
        current_user=FakeCurrentUser(),
        session_id=session_id,
        cage_id=cage_id,
        request=UpdateCageModeRequest(mode="PAUSE"),
        use_case=use_case,
    )

    assert response.message == "Modo de jaula actualizado para próximas visitas"
    assert response.cage_id == cage_id
    assert response.previous_mode == "NORMAL"
    assert response.new_mode == "PAUSE"
    assert response.applied_immediately is False
    assert use_case.calls == [(session_id, cage_id, "PAUSE", FakeCurrentUser.id)]


@pytest.mark.asyncio
async def test_patch_cyclic_cage_amount_response_contract():
    session_id = str(uuid4())
    cage_id = str(uuid4())
    use_case = _UpdateCyclicCageAmountUseCase()

    response = await update_cyclic_cage_amount(
        current_user=FakeCurrentUser(),
        session_id=session_id,
        cage_id=cage_id,
        request=UpdateAmountRequest(amount_kg=52.0),
        use_case=use_case,
    )

    assert response.message == "Cantidad de alimentación de jaula actualizada"
    assert response.new_amount_kg == 52.0
    assert use_case.calls == [(session_id, cage_id, 52.0)]


@pytest.mark.asyncio
async def test_patch_cyclic_cage_rate_response_contract():
    session_id = str(uuid4())
    cage_id = str(uuid4())
    use_case = _UpdateCyclicCageRateUseCase()

    response = await update_cyclic_cage_rate(
        current_user=FakeCurrentUser(),
        session_id=session_id,
        cage_id=cage_id,
        request=UpdateRateRequest(rate_kg_per_min=4.5),
        use_case=use_case,
    )

    assert response.message == "Tasa de alimentación de jaula actualizada"
    assert response.new_rate_kg_per_min == 4.5
    assert use_case.calls == [(session_id, cage_id, 4.5)]


@pytest.mark.asyncio
async def test_patch_cyclic_cage_amount_maps_value_error_to_400():
    with pytest.raises(HTTPException) as exc_info:
        await update_cyclic_cage_amount(
            current_user=FakeCurrentUser(),
            session_id=str(uuid4()),
            cage_id=str(uuid4()),
            request=UpdateAmountRequest(amount_kg=52.0),
            use_case=_FailingUseCase(),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "bad request"


@pytest.mark.asyncio
async def test_cyclic_status_exposes_per_cage_visits_and_total_rounds():
    session, first, second = _cyclic_session_with_cages()

    response = await get_cyclic_feeding_status(
        current_user=FakeCurrentUser(),
        session_id=session.id,
        session_repo=_SessionRepo(session),
        cage_feeding_repo=_CageFeedingRepo([first, second]),
        cage_repo=_CageRepo(),
        line_repo=_LineRepo(),
        machine=_Machine(),
    )

    assert response.session_id == session.id
    assert response.total_rounds == 15
    assert response.current_round == 2
    assert response.active_cage is not None
    assert response.active_cage.cage_id == first.cage_id
    assert response.active_cage.total_visits == 15
    assert {
        cage.cage_id: (cage.mode, cage.programmed_visits, cage.completed_visits) for cage in response.cages_summary
    } == {
        first.cage_id: ("NORMAL", 15, 1),
        second.cage_id: ("PAUSE", 10, 0),
    }


@pytest.mark.asyncio
async def test_history_detail_includes_cage_mode_change_and_per_cage_visit_totals():
    session, first, second = _cyclic_session_with_cages()
    first.increment_completed_visits()
    first.add_dispensed_amount(10.0)

    events = [
        FeedingEvent.session_started(session.id, session.operator_id),
        FeedingEvent.cage_mode_changed(
            feeding_session_id=session.id,
            cage_id=second.cage_id,
            previous_mode="NORMAL",
            new_mode="PAUSE",
            operator_id=str(uuid4()),
            applied_immediately=False,
        ),
        FeedingEvent.visit_completed(
            feeding_session_id=session.id,
            cage_id=first.cage_id,
            visit_number=1,
            cycle_number=1,
            dispensed_grams=10_000,
            duration_seconds=30,
        ),
    ]

    inventory_repo = type(
        "_InventoryRepo",
        (),
        {"list_session_consumptions": AsyncMock(return_value=[])},
    )()
    response = await get_session_history_detail(
        current_user=FakeCurrentUser(),
        session_id=session.id,
        session_repo=_SessionRepo(session),
        event_repo=_EventRepo(events),
        line_repo=_LineRepo(),
        cage_repo=_CageRepo(),
        inventory_repo=inventory_repo,
        user_repo=_UserRepo(),
    )

    assert response.type == "CYCLIC"
    assert {cage.cage_id: (cage.mode, cage.programmed_visits, cage.completed_visits) for cage in response.cages} == {
        first.cage_id: ("NORMAL", 15, 2),
        second.cage_id: ("PAUSE", 10, 0),
    }
    mode_change_events = [
        event for event in response.timeline if event.event_type == FeedingEventType.CAGE_MODE_CHANGED.value
    ]
    assert len(mode_change_events) == 1
    assert mode_change_events[0].data["cage_id"] == second.cage_id
    assert mode_change_events[0].data["new_mode"] == "PAUSE"
    assert mode_change_events[0].data["applied_immediately"] is False


@pytest.mark.asyncio
async def test_cage_visit_history_preserves_empty_visit_flags_and_zero_dispensed():
    session, first, _second = _cyclic_session_with_cages()
    events = [
        FeedingEvent.visit_completed(
            feeding_session_id=session.id,
            cage_id=first.cage_id,
            visit_number=1,
            cycle_number=1,
            dispensed_grams=10_000,
            duration_seconds=30,
        ),
        FeedingEvent.visit_completed(
            feeding_session_id=session.id,
            cage_id=first.cage_id,
            visit_number=11,
            cycle_number=1,
            dispensed_grams=0,
            duration_seconds=8,
            is_empty_visit=True,
        ),
    ]

    response = await get_cage_visit_history(
        current_user=FakeCurrentUser(),
        session_id=session.id,
        cage_id=first.cage_id,
        event_repo=_EventRepo(events),
        cage_repo=_CageRepo(),
    )

    assert response.total_dispensed_kg == 10.0
    assert response.avg_duration_seconds == 19.0
    assert [(visit.visit_number, visit.dispensed_kg, visit.is_empty_visit) for visit in response.visits] == [
        (1, 10.0, False),
        (11, 0.0, True),
    ]
