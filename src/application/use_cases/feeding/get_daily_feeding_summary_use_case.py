from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from application.dtos.feeding_history_dtos import (
    DailyFeedingSummaryDTO,
    DailyFeedingSummaryPointDTO,
)
from domain.entities.feeding_session import SessionStatus
from domain.repositories import IFeedingSessionRepository, ISystemConfigRepository


class GetDailyFeedingSummaryUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        system_config_repository: ISystemConfigRepository,
    ) -> None:
        self._session_repository = session_repository
        self._system_config_repository = system_config_repository

    async def execute(
        self,
        start_date: date,
        end_date: date,
        line_id: str | None = None,
        feeding_type: str | None = None,
        operator_id: str | None = None,
    ) -> DailyFeedingSummaryDTO:
        if end_date < start_date:
            raise ValueError("end_date debe ser mayor o igual a start_date")

        system_config = await self._system_config_repository.get()
        tz = ZoneInfo(system_config.timezone_id)

        range_start = datetime.combine(start_date, time.min, tzinfo=tz).astimezone(timezone.utc)
        range_end = datetime.combine(end_date, time.max, tzinfo=tz).astimezone(timezone.utc)
        sessions = await self._session_repository.list_by_date_range(range_start, range_end)

        points_by_date = self._empty_points(start_date, end_date)

        for session in sessions:
            if line_id and session.line_id != line_id:
                continue
            if feeding_type and session.type.value != feeding_type:
                continue
            if operator_id and session.operator_id != operator_id:
                continue
            if not session.actual_start:
                continue

            local_date = self._to_local_date(session.actual_start, tz)
            point = points_by_date.get(local_date)
            if point is None:
                continue

            point.total_dispensed_kg += session.total_dispensed_kg
            point.total_programmed_kg += session.total_programmed_kg

            if session.status == SessionStatus.COMPLETED:
                point.sessions_completed += 1
            elif session.status == SessionStatus.CANCELLED:
                point.sessions_cancelled += 1
            elif session.status == SessionStatus.INTERRUPTED:
                point.sessions_interrupted += 1

        points = [
            DailyFeedingSummaryPointDTO(
                date=point.date,
                total_dispensed_kg=round(point.total_dispensed_kg, 2),
                total_programmed_kg=round(point.total_programmed_kg, 2),
                sessions_completed=point.sessions_completed,
                sessions_cancelled=point.sessions_cancelled,
                sessions_interrupted=point.sessions_interrupted,
            )
            for point in points_by_date.values()
        ]

        return DailyFeedingSummaryDTO(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            points=points,
        )

    def _empty_points(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[date, DailyFeedingSummaryPointDTO]:
        points: dict[date, DailyFeedingSummaryPointDTO] = {}
        current_date = start_date
        while current_date <= end_date:
            points[current_date] = DailyFeedingSummaryPointDTO(
                date=current_date.isoformat(),
                total_dispensed_kg=0.0,
                total_programmed_kg=0.0,
                sessions_completed=0,
                sessions_cancelled=0,
                sessions_interrupted=0,
            )
            current_date += timedelta(days=1)
        return points

    def _to_local_date(self, value: datetime, tz: ZoneInfo) -> date:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(tz).date()
