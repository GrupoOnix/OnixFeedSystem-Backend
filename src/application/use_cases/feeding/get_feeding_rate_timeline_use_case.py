from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from math import ceil
from zoneinfo import ZoneInfo

from application.dtos.feeding_rate_timeline_dtos import (
    FeedingRateTimelineDTO,
    RateTimelinePointDTO,
    RateTimelineSeriesDTO,
    RateTimelineSummaryDTO,
    TotalRateTimelinePointDTO,
)
from domain.dtos.feeding_rate_timeline import FeedingRateTimelineVisit
from domain.repositories import (
    ICageRepository,
    IFeedingEventRepository,
    IFeedingLineRepository,
    ISystemConfigRepository,
)
from domain.value_objects import CageId, LineId


@dataclass
class _TimelineBucket:
    dispensed_kg: float = 0.0
    active_sessions: set[str] = field(default_factory=set)


class GetFeedingRateTimelineUseCase:
    _COLOR_HINTS = [
        "#2563eb",
        "#16a34a",
        "#dc2626",
        "#9333ea",
        "#0891b2",
        "#ea580c",
        "#4f46e5",
        "#0f766e",
    ]

    def __init__(
        self,
        event_repository: IFeedingEventRepository,
        system_config_repository: ISystemConfigRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
    ) -> None:
        self._event_repository = event_repository
        self._system_config_repository = system_config_repository
        self._line_repository = line_repository
        self._cage_repository = cage_repository

    async def execute(
        self,
        start_at: datetime,
        end_at: datetime,
        line_id: str | None = None,
        cage_id: str | None = None,
        feeding_type: str | None = None,
        bucket_seconds: int = 60,
        include_series: str = "lines",
        operator_id: str | None = None,
    ) -> FeedingRateTimelineDTO:
        if end_at <= start_at:
            raise ValueError("end_at debe ser mayor que start_at")
        if bucket_seconds <= 0:
            raise ValueError("bucket_seconds debe ser mayor a 0")
        if include_series not in {"lines", "cages", "sessions"}:
            raise ValueError("include_series debe ser lines, cages o sessions")

        start_at = self._as_utc(start_at)
        end_at = self._as_utc(end_at)
        bucket_count = ceil((end_at - start_at).total_seconds() / bucket_seconds)
        if bucket_count > 10000:
            raise ValueError("El rango solicitado genera demasiados buckets")

        system_config = await self._system_config_repository.get()
        timezone_id = system_config.timezone_id
        ZoneInfo(timezone_id)

        visit_filters = {
            "start": start_at,
            "end": end_at,
            "line_id": line_id,
            "cage_id": cage_id,
            "feeding_type": feeding_type,
        }
        if operator_id:
            visit_filters["operator_id"] = operator_id
        visits = await self._event_repository.list_rate_timeline_visits(**visit_filters)

        total_buckets = [_TimelineBucket() for _ in range(bucket_count)]
        series_buckets: dict[str, dict[int, _TimelineBucket]] = {}
        series_meta: dict[str, tuple[str, str]] = {}

        for visit in visits:
            self._apply_visit_to_buckets(
                visit=visit,
                start_at=start_at,
                end_at=end_at,
                bucket_seconds=bucket_seconds,
                total_buckets=total_buckets,
                series_buckets=series_buckets,
                series_meta=series_meta,
                include_series=include_series,
            )

        total_series = self._build_total_series(
            start_at=start_at,
            bucket_seconds=bucket_seconds,
            total_buckets=total_buckets,
        )
        named_series = await self._build_series(
            start_at=start_at,
            bucket_seconds=bucket_seconds,
            series_buckets=series_buckets,
            series_meta=series_meta,
        )

        total_dispensed_kg = sum(bucket.dispensed_kg for bucket in total_buckets)
        active_bucket_count = sum(1 for bucket in total_buckets if bucket.dispensed_kg > 0)
        active_minutes = ceil(active_bucket_count * bucket_seconds / 60) if active_bucket_count else 0
        peak_point = max(total_series, key=lambda point: point.rate_kg_per_min, default=None)
        peak_rate = peak_point.rate_kg_per_min if peak_point else 0.0

        return FeedingRateTimelineDTO(
            start_at=start_at,
            end_at=end_at,
            bucket_seconds=bucket_seconds,
            timezone=timezone_id,
            summary=RateTimelineSummaryDTO(
                total_dispensed_kg=round(total_dispensed_kg, 3),
                active_minutes=active_minutes,
                avg_active_rate_kg_per_min=round(total_dispensed_kg / active_minutes, 3) if active_minutes else 0.0,
                peak_total_rate_kg_per_min=round(peak_rate, 3),
                peak_total_rate_at=peak_point.timestamp if peak_point and peak_rate > 0 else None,
                max_overlapping_sessions=max(
                    (len(bucket.active_sessions) for bucket in total_buckets),
                    default=0,
                ),
            ),
            total_series=total_series,
            series=named_series,
        )

    def _apply_visit_to_buckets(
        self,
        visit: FeedingRateTimelineVisit,
        start_at: datetime,
        end_at: datetime,
        bucket_seconds: int,
        total_buckets: list[_TimelineBucket],
        series_buckets: dict[str, dict[int, _TimelineBucket]],
        series_meta: dict[str, tuple[str, str]],
        include_series: str,
    ) -> None:
        completed_at = self._as_utc(visit.completed_at)
        visit_start = completed_at - timedelta(seconds=visit.duration_seconds)
        overlap_start = max(visit_start, start_at)
        overlap_end = min(completed_at, end_at)
        if overlap_end <= overlap_start:
            return

        first_bucket = int((overlap_start - start_at).total_seconds() // bucket_seconds)
        last_bucket = int((overlap_end - start_at).total_seconds() // bucket_seconds)
        if overlap_end == start_at + timedelta(seconds=last_bucket * bucket_seconds):
            last_bucket -= 1

        group_id, kind = self._group_for_visit(visit, include_series)
        series_meta.setdefault(group_id, (kind, group_id))
        group_buckets = series_buckets.setdefault(group_id, {})

        for bucket_index in range(max(first_bucket, 0), min(last_bucket + 1, len(total_buckets))):
            bucket_start = start_at + timedelta(seconds=bucket_index * bucket_seconds)
            bucket_end = bucket_start + timedelta(seconds=bucket_seconds)
            seconds = (min(overlap_end, bucket_end) - max(overlap_start, bucket_start)).total_seconds()
            if seconds <= 0:
                continue

            dispensed_kg = visit.dispensed_kg * seconds / visit.duration_seconds
            total_buckets[bucket_index].dispensed_kg += dispensed_kg
            total_buckets[bucket_index].active_sessions.add(visit.session_id)

            group_bucket = group_buckets.setdefault(bucket_index, _TimelineBucket())
            group_bucket.dispensed_kg += dispensed_kg
            group_bucket.active_sessions.add(visit.session_id)

    def _build_total_series(
        self,
        start_at: datetime,
        bucket_seconds: int,
        total_buckets: list[_TimelineBucket],
    ) -> list[TotalRateTimelinePointDTO]:
        return [
            TotalRateTimelinePointDTO(
                timestamp=start_at + timedelta(seconds=index * bucket_seconds),
                rate_kg_per_min=round(bucket.dispensed_kg / (bucket_seconds / 60), 3),
                active_sessions=len(bucket.active_sessions),
            )
            for index, bucket in enumerate(total_buckets)
        ]

    async def _build_series(
        self,
        start_at: datetime,
        bucket_seconds: int,
        series_buckets: dict[str, dict[int, _TimelineBucket]],
        series_meta: dict[str, tuple[str, str]],
    ) -> list[RateTimelineSeriesDTO]:
        series: list[RateTimelineSeriesDTO] = []
        for position, (series_id, buckets) in enumerate(sorted(series_buckets.items())):
            kind, fallback_name = series_meta[series_id]
            series.append(
                RateTimelineSeriesDTO(
                    id=series_id,
                    name=await self._resolve_name(series_id, kind, fallback_name),
                    kind=kind,
                    color_hint=self._COLOR_HINTS[position % len(self._COLOR_HINTS)],
                    points=[
                        RateTimelinePointDTO(
                            timestamp=start_at + timedelta(seconds=index * bucket_seconds),
                            rate_kg_per_min=round(bucket.dispensed_kg / (bucket_seconds / 60), 3),
                            dispensed_kg=round(bucket.dispensed_kg, 3),
                            active_sessions=len(bucket.active_sessions),
                        )
                        for index, bucket in sorted(buckets.items())
                    ],
                )
            )
        return series

    async def _resolve_name(self, item_id: str, kind: str, fallback_name: str) -> str:
        if kind == "LINE":
            line = await self._line_repository.find_by_id(LineId.from_string(item_id))
            return line.name.value if line else fallback_name
        if kind == "CAGE":
            cage = await self._cage_repository.find_by_id(CageId.from_string(item_id))
            return cage.name.value if cage else fallback_name
        return f"Sesión {item_id[:8]}"

    def _group_for_visit(self, visit: FeedingRateTimelineVisit, include_series: str) -> tuple[str, str]:
        if include_series == "cages":
            return visit.cage_id, "CAGE"
        if include_series == "sessions":
            return visit.session_id, "SESSION"
        return visit.line_id, "LINE"

    def _as_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
