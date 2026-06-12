"""Seed completed fake feeding sessions for the last 30 days.

Run from the repository root:
    python src/scripts/seed_weekly_feeding_history.py
"""

from __future__ import annotations

import asyncio
import random
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from sqlalchemy import or_, select
from sqlmodel import col

SRC_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))
load_dotenv(REPO_ROOT / ".env")

from infrastructure.persistence.database import async_session_maker, close_db_connection  # noqa: E402
from infrastructure.persistence.models.cage_feeding_model import CageFeedingModel  # noqa: E402
from infrastructure.persistence.models.cage_model import CageModel  # noqa: E402
from infrastructure.persistence.models.doser_model import DoserModel  # noqa: E402
from infrastructure.persistence.models.feeding_event_model import FeedingEventModel  # noqa: E402
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel  # noqa: E402
from infrastructure.persistence.models.feeding_session_model import FeedingSessionModel  # noqa: E402
from infrastructure.persistence.models.silo_model import SiloModel  # noqa: E402
from infrastructure.persistence.models.slot_assignment_model import SlotAssignmentModel  # noqa: E402
from infrastructure.persistence.models.system_config_model import SystemConfigModel  # noqa: E402

SEED_OPERATOR_ID = "00000000-0000-0000-0000-00000000feed"
RANDOM_SEED = 20260522
MORNING_DURATION_RANGE_SECONDS = (3_600, 10_800)
MIDDAY_DURATION_RANGE_SECONDS = (7_200, 18_000)


@dataclass(frozen=True)
class FeedingTarget:
    cage_id: UUID
    slot_number: int
    programmed_kg: float
    visits: int
    rate_kg_per_min: float


@dataclass(frozen=True)
class FeedingWindow:
    session_number: int
    start_time: time
    min_duration_seconds: int
    max_duration_seconds: int


async def main() -> None:
    random.seed(RANDOM_SEED)

    async with async_session_maker() as session:
        timezone_id = await _get_timezone_id(session)
        tz = ZoneInfo(timezone_id)
        now_local = datetime.now(tz)

        lines = (
            await session.execute(select(FeedingLineModel).order_by(col(FeedingLineModel.name)))
        ).scalars().all()
        if not lines:
            raise RuntimeError(
                "No hay feeding_lines. Crea/sincroniza el trazado del sistema antes de ejecutar el seed."
            )

        lines_processed = 0
        lines_skipped_without_targets = 0
        sessions_created = 0
        sessions_skipped_future = 0
        sessions_skipped_overlap = 0
        cage_feedings_created = 0
        events_created = 0

        for line in lines:
            targets = await _build_targets(session, line.id)
            if not targets:
                lines_skipped_without_targets += 1
                continue

            lines_processed += 1
            doser = (
                await session.execute(
                    select(DoserModel)
                    .where(col(DoserModel.line_id) == line.id)
                    .order_by(col(DoserModel.name))
                )
            ).scalars().first()
            silo_id = doser.silo_id if doser and doser.silo_id else await _get_first_silo_id(session)

            for day in _last_30_dates(now_local):
                for feeding_window in _feeding_windows():
                    start_local = datetime.combine(day, feeding_window.start_time, tzinfo=tz)
                    if start_local >= now_local - timedelta(minutes=10):
                        continue

                    selected_targets = _select_targets(targets, feeding_window.session_number)
                    session_model, cage_feeding_models, event_models = _make_completed_session(
                        line_id=line.id,
                        doser_id=doser.id if doser else None,
                        silo_id=silo_id,
                        targets=selected_targets,
                        session_number=feeding_window.session_number,
                        start_local=start_local,
                        min_duration_seconds=feeding_window.min_duration_seconds,
                        max_duration_seconds=feeding_window.max_duration_seconds,
                    )

                    actual_start = session_model.actual_start
                    actual_end = session_model.actual_end
                    if actual_start is None or actual_end is None:
                        raise RuntimeError("La sesión generada no tiene rango temporal completo.")

                    if actual_end >= now_local.astimezone(timezone.utc) - timedelta(minutes=10):
                        sessions_skipped_future += 1
                        continue

                    if await _has_overlapping_session(
                        session=session,
                        line_id=line.id,
                        start_utc=actual_start,
                        end_utc=actual_end,
                    ):
                        sessions_skipped_overlap += 1
                        continue

                    session.add(session_model)
                    session.add_all(cage_feeding_models)
                    session.add_all(event_models)
                    sessions_created += 1
                    cage_feedings_created += len(cage_feeding_models)
                    events_created += len(event_models)

        await session.commit()

    await close_db_connection()
    print(
        "Seed completado: "
        f"{lines_processed} lineas procesadas, "
        f"{lines_skipped_without_targets} lineas sin jaulas, "
        f"{sessions_created} sesiones, "
        f"{sessions_skipped_future} sesiones omitidas por no haber terminado, "
        f"{sessions_skipped_overlap} sesiones omitidas por solape, "
        f"{cage_feedings_created} alimentaciones de jaula, "
        f"{events_created} eventos. "
        f"operator_id={SEED_OPERATOR_ID}"
    )


async def _get_timezone_id(session) -> str:
    config = (
        await session.execute(select(SystemConfigModel).where(col(SystemConfigModel.id) == 1))
    ).scalars().first()
    return config.timezone_id if config else "America/Santiago"


async def _build_targets(session, line_id: UUID) -> list[FeedingTarget]:
    assignments = (
        await session.execute(
            select(SlotAssignmentModel)
            .where(col(SlotAssignmentModel.line_id) == line_id)
            .order_by(col(SlotAssignmentModel.slot_number))
        )
    ).scalars().all()

    if assignments:
        cage_ids = [assignment.cage_id for assignment in assignments]
        cages = (
            await session.execute(select(CageModel).where(col(CageModel.id).in_(cage_ids)))
        ).scalars().all()
        cages_by_id = {cage.id: cage for cage in cages}
        return [
            _target_from_cage(cages_by_id[assignment.cage_id], assignment.slot_number)
            for assignment in assignments
            if assignment.cage_id in cages_by_id
        ]

    cages = (
        await session.execute(select(CageModel).order_by(col(CageModel.name)).limit(6))
    ).scalars().all()
    return [_target_from_cage(cage, index) for index, cage in enumerate(cages, start=1)]


async def _get_first_silo_id(session) -> UUID | None:
    silo = (
        await session.execute(select(SiloModel).order_by(col(SiloModel.name)))
    ).scalars().first()
    return silo.id if silo else None


async def _has_overlapping_session(
    session,
    line_id: UUID,
    start_utc: datetime,
    end_utc: datetime,
) -> bool:
    existing_id = (
        await session.execute(
            select(col(FeedingSessionModel.id))
            .where(
                col(FeedingSessionModel.line_id) == line_id,
                col(FeedingSessionModel.actual_start) < end_utc,
                or_(
                    col(FeedingSessionModel.actual_end).is_(None),
                    col(FeedingSessionModel.actual_end) > start_utc,
                ),
            )
            .limit(1)
        )
    ).scalars().first()
    return existing_id is not None


def _target_from_cage(cage: CageModel, slot_number: int) -> FeedingTarget:
    daily_target = cage.daily_feeding_target_kg or random.uniform(18.0, 42.0)
    programmed_kg = round(daily_target * random.uniform(0.28, 0.42), 2)
    visits = random.choice((2, 3, 4))
    rate = round(random.uniform(4.5, 8.5), 2)
    return FeedingTarget(
        cage_id=cage.id,
        slot_number=slot_number,
        programmed_kg=max(programmed_kg, 5.0),
        visits=visits,
        rate_kg_per_min=rate,
    )


def _last_30_dates(now_local: datetime) -> list[date]:
    start_date = now_local.date() - timedelta(days=29)
    return [start_date + timedelta(days=offset) for offset in range(30)]


def _feeding_windows() -> list[FeedingWindow]:
    return [
        FeedingWindow(
            session_number=1,
            start_time=_morning_start_time(),
            min_duration_seconds=MORNING_DURATION_RANGE_SECONDS[0],
            max_duration_seconds=MORNING_DURATION_RANGE_SECONDS[1],
        ),
        FeedingWindow(
            session_number=2,
            start_time=_midday_start_time(),
            min_duration_seconds=MIDDAY_DURATION_RANGE_SECONDS[0],
            max_duration_seconds=MIDDAY_DURATION_RANGE_SECONDS[1],
        ),
    ]


def _morning_start_time() -> time:
    minute_offset = random.randint(-15, 15)
    start = datetime.combine(datetime.today(), time(8, 0)) + timedelta(minutes=minute_offset)
    return start.time().replace(second=random.randint(0, 59), microsecond=0)


def _midday_start_time() -> time:
    minute_offset = random.randint(-15, 15)
    start = datetime.combine(datetime.today(), time(12, 0)) + timedelta(minutes=minute_offset)
    return start.time().replace(second=random.randint(0, 59), microsecond=0)


def _select_targets(targets: list[FeedingTarget], session_number: int) -> list[FeedingTarget]:
    if len(targets) <= 3:
        return targets

    rotated = targets[session_number - 1 :] + targets[: session_number - 1]
    target_count = min(len(rotated), random.choice((3, 4, 5)))
    return rotated[:target_count]


def _make_completed_session(
    line_id: UUID,
    doser_id: UUID | None,
    silo_id: UUID | None,
    targets: list[FeedingTarget],
    session_number: int,
    start_local: datetime,
    min_duration_seconds: int,
    max_duration_seconds: int,
) -> tuple[FeedingSessionModel, list[CageFeedingModel], list[FeedingEventModel]]:
    session_id = str(uuid4())
    start_utc = start_local.astimezone(timezone.utc)
    duration_seconds = random.randint(min_duration_seconds, max_duration_seconds)
    end_utc = start_utc + timedelta(seconds=duration_seconds)

    cage_feedings: list[CageFeedingModel] = []
    events: list[FeedingEventModel] = [
        _event(session_id, "session_started", start_utc, {"operator_id": SEED_OPERATOR_ID, "seed": True})
    ]

    total_programmed = 0.0
    total_dispensed = 0.0
    visit_events_data: list[tuple[FeedingTarget, int, float]] = []

    for order, target in enumerate(targets, start=1):
        programmed_kg = round(target.programmed_kg * random.uniform(0.9, 1.15), 2)
        dispensed_kg = round(programmed_kg * random.uniform(0.94, 1.03), 2)
        visits = target.visits
        visit_kg = dispensed_kg / visits

        cage_feedings.append(
            CageFeedingModel(
                id=str(uuid4()),
                feeding_session_id=session_id,
                cage_id=target.cage_id,
                doser_id=doser_id,
                silo_id=silo_id,
                execution_order=order,
                mode="NORMAL",
                programmed_kg=programmed_kg,
                programmed_visits=visits,
                rate_kg_per_min=target.rate_kg_per_min,
                dispensed_kg=dispensed_kg,
                completed_visits=visits,
                status="COMPLETED",
                created_at=start_utc,
            )
        )

        for visit_number in range(1, visits + 1):
            visit_events_data.append((target, visit_number, visit_kg))

        total_programmed += programmed_kg
        total_dispensed += dispensed_kg

    total_visits = len(visit_events_data)
    if total_visits:
        active_start_offset = random.randint(3 * 60, 8 * 60)
        active_end_offset = duration_seconds - random.randint(2 * 60, 6 * 60)
        active_window_seconds = active_end_offset - active_start_offset
        pauses: list[float] = [random.randint(60, 240) for _ in range(total_visits - 1)]
        pauses_total = sum(pauses)

        max_pause_total = active_window_seconds * 0.25
        if pauses_total > max_pause_total and pauses_total > 0:
            pause_scale = max_pause_total / pauses_total
            pauses = [pause * pause_scale for pause in pauses]
            pauses_total = sum(pauses)

        available_feeding_seconds = active_window_seconds - pauses_total
        duration_weights = [random.uniform(0.75, 1.25) for _ in range(total_visits)]
        weight_total = sum(duration_weights)
        visit_durations = [
            max(60.0, available_feeding_seconds * weight / weight_total)
            for weight in duration_weights
        ]

        cursor = start_utc + timedelta(seconds=active_start_offset)
        for index, (target, visit_number, visit_kg) in enumerate(visit_events_data):
            visit_duration_seconds = visit_durations[index]
            visit_started_at = cursor
            visit_completed_at = visit_started_at + timedelta(seconds=visit_duration_seconds)

            events.append(
                _event(
                    session_id,
                    "visit_started",
                    visit_started_at,
                    {
                        "cage_id": str(target.cage_id),
                        "visit_number": visit_number,
                        "cycle_number": visit_number,
                        "is_empty_visit": False,
                    },
                )
            )
            if index < len(pauses):
                cursor = visit_completed_at + timedelta(seconds=pauses[index])
            events.append(
                _event(
                    session_id,
                    "visit_completed",
                    visit_completed_at,
                    {
                        "cage_id": str(target.cage_id),
                        "visit_number": visit_number,
                        "cycle_number": visit_number,
                        "dispensed_grams": round(visit_kg * 1000, 2),
                        "duration_seconds": round(visit_duration_seconds, 2),
                        "is_empty_visit": False,
                    },
                )
            )

    for rate_change in _rate_change_events(session_id, start_utc, end_utc, targets):
        events.append(rate_change)

    events.append(
        _event(
            session_id,
            "session_completed",
            end_utc,
            {
                "total_dispensed_kg": round(total_dispensed, 2),
                "duration_seconds": round(duration_seconds, 2),
                "completion_reason": "natural",
                "completed_by": "system",
                "seed": True,
            },
        )
    )

    feeding_session = FeedingSessionModel(
        id=session_id,
        line_id=line_id,
        operator_id=SEED_OPERATOR_ID,
        type="CYCLIC" if len(targets) > 1 else "MANUAL",
        status="COMPLETED",
        allow_overtime=False,
        total_programmed_kg=round(total_programmed, 2),
        scheduled_start=start_utc,
        actual_start=start_utc,
        actual_end=end_utc,
        created_at=start_utc,
    )

    return feeding_session, cage_feedings, events


def _rate_change_events(
    session_id: str,
    start_utc: datetime,
    end_utc: datetime,
    targets: list[FeedingTarget],
) -> list[FeedingEventModel]:
    if not targets:
        return []

    event_count = random.randint(0, 5)
    if event_count == 0:
        return []

    duration_seconds = (end_utc - start_utc).total_seconds()
    change_offsets = sorted(random.uniform(20 * 60, duration_seconds - 20 * 60) for _ in range(event_count))
    current_rate = random.choice(targets).rate_kg_per_min

    events = []
    for offset in change_offsets:
        changed_target = random.choice(targets)
        previous_rate = current_rate
        current_rate = round(max(0.5, previous_rate * random.uniform(0.75, 1.25)), 2)
        events.append(
            _event(
                session_id,
                "rate_changed",
                start_utc + timedelta(seconds=offset),
                {
                    "cage_id": str(changed_target.cage_id),
                    "previous_rate": previous_rate,
                    "new_rate": current_rate,
                    "applied_immediately": True,
                },
            )
        )
    return events


def _event(session_id: str, event_type: str, timestamp: datetime, data: dict) -> FeedingEventModel:
    return FeedingEventModel(
        id=str(uuid4()),
        feeding_session_id=session_id,
        event_type=event_type,
        timestamp=timestamp,
        data=data,
    )


if __name__ == "__main__":
    asyncio.run(main())
