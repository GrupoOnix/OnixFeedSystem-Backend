import pytest

from application.services import feeding_orchestrator
from application.services.feeding_orchestrator import FeedingOrchestrator
from domain.value_objects import BlowerPowerPercentage, LineId


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
