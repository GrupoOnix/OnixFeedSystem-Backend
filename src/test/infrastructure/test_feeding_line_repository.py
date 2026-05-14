from types import SimpleNamespace

import pytest

from domain.aggregates.feeding_line import FeedingLine
from domain.enums import FeedingLineStatus
from domain.exceptions import FeedingLineUnavailableException
from domain.value_objects import LineId, LineName
from infrastructure.persistence.repositories.feeding_line_repository import (
    FeedingLineRepository,
)


class FakeSession:
    def __init__(self, rowcount, current_status=None):
        self._results = [
            SimpleNamespace(rowcount=rowcount),
            SimpleNamespace(scalar_one_or_none=lambda: current_status),
        ]
        self.executed = []
        self.flushed = False

    async def execute(self, stmt):
        self.executed.append(stmt)
        return self._results.pop(0)

    async def flush(self):
        self.flushed = True


def make_reserved_line(status=FeedingLineStatus.FEEDING):
    line = FeedingLine(name=LineName("Linea Test"))
    line._id = LineId.generate()
    line._status = status
    line._locked_by = "operator"
    line._locked_reason = "feeding"
    return line


@pytest.mark.asyncio
async def test_available_status_transition_flushes_when_update_matches():
    session = FakeSession(rowcount=1)
    repository = FeedingLineRepository(session)

    await repository.save_available_status_transition(make_reserved_line())

    assert session.flushed is True
    assert len(session.executed) == 1


@pytest.mark.asyncio
async def test_available_status_transition_raises_when_update_does_not_match():
    session = FakeSession(rowcount=0, current_status=FeedingLineStatus.MANUAL_CONTROL.value)
    repository = FeedingLineRepository(session)

    with pytest.raises(FeedingLineUnavailableException, match="MANUAL_CONTROL"):
        await repository.save_available_status_transition(make_reserved_line())

    assert session.flushed is False
    assert len(session.executed) == 2
