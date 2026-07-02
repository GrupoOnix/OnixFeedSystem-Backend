from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from application.use_cases.feeding.get_feeding_rate_timeline_use_case import (
    GetFeedingRateTimelineUseCase,
)
from domain.dtos.feeding_rate_timeline import FeedingRateTimelineVisit


class FakeEventRepository:
    def __init__(self, visits):
        self.visits = visits
        self.calls = []

    async def list_rate_timeline_visits(self, **kwargs):
        self.calls.append(kwargs)
        return self.visits


class FakeSystemConfigRepository:
    async def get(self):
        return SimpleNamespace(timezone_id="America/Santiago")


class FakeLineRepository:
    async def find_by_id(self, line_id):
        return SimpleNamespace(name=SimpleNamespace(value="Linea 1"))


class FakeCageRepository:
    async def find_by_id(self, cage_id):
        names = {
            "11111111-1111-1111-1111-111111111111": "Jaula 1",
            "22222222-2222-2222-2222-222222222222": "Jaula 2",
        }
        return SimpleNamespace(name=SimpleNamespace(value=names[str(cage_id.value)]))


@pytest.mark.asyncio
async def test_rate_timeline_distributes_visit_kg_across_overlapping_buckets():
    line_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    cage_1 = "11111111-1111-1111-1111-111111111111"
    cage_2 = "22222222-2222-2222-2222-222222222222"
    visits = [
        FeedingRateTimelineVisit(
            session_id="session-a",
            feeding_type="MANUAL",
            line_id=line_id,
            cage_id=cage_1,
            completed_at=datetime(2026, 5, 28, 0, 2, tzinfo=timezone.utc),
            duration_seconds=120,
            dispensed_kg=4,
        ),
        FeedingRateTimelineVisit(
            session_id="session-b",
            feeding_type="MANUAL",
            line_id=line_id,
            cage_id=cage_2,
            completed_at=datetime(2026, 5, 28, 0, 2, tzinfo=timezone.utc),
            duration_seconds=60,
            dispensed_kg=3,
        ),
    ]
    use_case = GetFeedingRateTimelineUseCase(
        event_repository=FakeEventRepository(visits),
        system_config_repository=FakeSystemConfigRepository(),
        line_repository=FakeLineRepository(),
        cage_repository=FakeCageRepository(),
    )

    result = await use_case.execute(
        start_at=datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 5, 28, 0, 3, tzinfo=timezone.utc),
        bucket_seconds=60,
        include_series="lines",
    )

    assert [point.rate_kg_per_min for point in result.total_series] == [2.0, 5.0, 0.0]
    assert [point.active_sessions for point in result.total_series] == [1, 2, 0]
    assert result.summary.total_dispensed_kg == 7.0
    assert result.summary.active_minutes == 2
    assert result.summary.avg_active_rate_kg_per_min == 3.5
    assert result.summary.peak_total_rate_kg_per_min == 5.0
    assert result.summary.peak_total_rate_at == datetime(2026, 5, 28, 0, 1, tzinfo=timezone.utc)
    assert result.summary.max_overlapping_sessions == 2
    assert len(result.series) == 1
    assert result.series[0].id == line_id
    assert result.series[0].kind == "LINE"
    assert [point.dispensed_kg for point in result.series[0].points] == [2.0, 5.0]


@pytest.mark.asyncio
async def test_rate_timeline_can_group_individual_series_by_cage():
    line_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    cage_id = "11111111-1111-1111-1111-111111111111"
    use_case = GetFeedingRateTimelineUseCase(
        event_repository=FakeEventRepository(
            [
                FeedingRateTimelineVisit(
                    session_id="session-a",
                    feeding_type="CYCLIC",
                    line_id=line_id,
                    cage_id=cage_id,
                    completed_at=datetime(2026, 5, 28, 0, 1, tzinfo=timezone.utc),
                    duration_seconds=60,
                    dispensed_kg=1.5,
                )
            ]
        ),
        system_config_repository=FakeSystemConfigRepository(),
        line_repository=FakeLineRepository(),
        cage_repository=FakeCageRepository(),
    )

    result = await use_case.execute(
        start_at=datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 5, 28, 0, 2, tzinfo=timezone.utc),
        include_series="cages",
    )

    assert result.series[0].id == cage_id
    assert result.series[0].name == "Jaula 1"
    assert result.series[0].kind == "CAGE"
    assert result.series[0].points[0].rate_kg_per_min == 1.5
