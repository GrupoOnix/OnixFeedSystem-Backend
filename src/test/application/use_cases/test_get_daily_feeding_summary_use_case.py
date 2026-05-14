from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from application.use_cases.feeding.get_daily_feeding_summary_use_case import GetDailyFeedingSummaryUseCase
from domain.entities.feeding_session import FeedingType, SessionStatus


class FakeSession:
    def __init__(
        self,
        actual_start: datetime,
        line_id: str,
        feeding_type: FeedingType,
        status: SessionStatus,
        total_programmed_kg: float,
        total_dispensed_kg: float,
    ) -> None:
        self.actual_start = actual_start
        self.line_id = line_id
        self.type = feeding_type
        self.status = status
        self.total_programmed_kg = total_programmed_kg
        self.total_dispensed_kg = total_dispensed_kg


class FakeSessionRepository:
    def __init__(self, sessions: list[FakeSession]) -> None:
        self.sessions = sessions

    async def list_by_date_range(self, start: datetime, end: datetime) -> list[FakeSession]:
        return self.sessions


class FakeSystemConfigRepository:
    async def get(self) -> SimpleNamespace:
        return SimpleNamespace(timezone_id="America/Santiago")


@pytest.mark.asyncio
async def test_daily_summary_groups_by_system_local_date_and_fills_empty_days():
    use_case = GetDailyFeedingSummaryUseCase(
        session_repository=FakeSessionRepository(
            [
                FakeSession(
                    actual_start=datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc),
                    line_id="line-1",
                    feeding_type=FeedingType.MANUAL,
                    status=SessionStatus.COMPLETED,
                    total_programmed_kg=130.0,
                    total_dispensed_kg=120.5,
                ),
                FakeSession(
                    actual_start=datetime(2026, 5, 2, 2, 30, tzinfo=timezone.utc),
                    line_id="line-1",
                    feeding_type=FeedingType.MANUAL,
                    status=SessionStatus.INTERRUPTED,
                    total_programmed_kg=10.0,
                    total_dispensed_kg=4.0,
                ),
                FakeSession(
                    actual_start=datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
                    line_id="line-1",
                    feeding_type=FeedingType.MANUAL,
                    status=SessionStatus.CANCELLED,
                    total_programmed_kg=20.0,
                    total_dispensed_kg=0.0,
                ),
            ]
        ),
        system_config_repository=FakeSystemConfigRepository(),
    )

    summary = await use_case.execute(
        start_date=datetime(2026, 5, 1).date(),
        end_date=datetime(2026, 5, 3).date(),
    )

    assert summary.start_date == "2026-05-01"
    assert summary.end_date == "2026-05-03"
    assert [point.date for point in summary.points] == ["2026-05-01", "2026-05-02", "2026-05-03"]
    assert summary.points[0].total_dispensed_kg == 124.5
    assert summary.points[0].total_programmed_kg == 140.0
    assert summary.points[0].sessions_completed == 1
    assert summary.points[0].sessions_interrupted == 1
    assert summary.points[1].total_dispensed_kg == 0.0
    assert summary.points[2].sessions_cancelled == 1


@pytest.mark.asyncio
async def test_daily_summary_applies_line_and_type_filters():
    use_case = GetDailyFeedingSummaryUseCase(
        session_repository=FakeSessionRepository(
            [
                FakeSession(
                    actual_start=datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc),
                    line_id="line-1",
                    feeding_type=FeedingType.MANUAL,
                    status=SessionStatus.COMPLETED,
                    total_programmed_kg=10.0,
                    total_dispensed_kg=9.0,
                ),
                FakeSession(
                    actual_start=datetime(2026, 5, 1, 15, 0, tzinfo=timezone.utc),
                    line_id="line-2",
                    feeding_type=FeedingType.MANUAL,
                    status=SessionStatus.COMPLETED,
                    total_programmed_kg=20.0,
                    total_dispensed_kg=18.0,
                ),
                FakeSession(
                    actual_start=datetime(2026, 5, 1, 16, 0, tzinfo=timezone.utc),
                    line_id="line-1",
                    feeding_type=FeedingType.CYCLIC,
                    status=SessionStatus.COMPLETED,
                    total_programmed_kg=30.0,
                    total_dispensed_kg=27.0,
                ),
            ]
        ),
        system_config_repository=FakeSystemConfigRepository(),
    )

    summary = await use_case.execute(
        start_date=datetime(2026, 5, 1).date(),
        end_date=datetime(2026, 5, 1).date(),
        line_id="line-1",
        feeding_type="MANUAL",
    )

    assert summary.points[0].total_dispensed_kg == 9.0
    assert summary.points[0].total_programmed_kg == 10.0
    assert summary.points[0].sessions_completed == 1


@pytest.mark.asyncio
async def test_daily_summary_rejects_inverted_date_range():
    use_case = GetDailyFeedingSummaryUseCase(
        session_repository=FakeSessionRepository([]),
        system_config_repository=FakeSystemConfigRepository(),
    )

    with pytest.raises(ValueError, match="end_date"):
        await use_case.execute(
            start_date=datetime(2026, 5, 2).date(),
            end_date=datetime(2026, 5, 1).date(),
        )
