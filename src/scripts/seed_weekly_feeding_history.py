"""Seed completed fake feeding sessions for the current week.

Run from the repository root:
    python src/scripts/seed_weekly_feeding_history.py
"""

from __future__ import annotations

import asyncio
import random
import sys
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from sqlalchemy import delete, select

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


@dataclass(frozen=True)
class FeedingTarget:
    cage_id: UUID
    slot_number: int
    programmed_kg: float
    visits: int
    rate_kg_per_min: float


async def main() -> None:
    random.seed(RANDOM_SEED)

    async with async_session_maker() as session:
        timezone_id = await _get_timezone_id(session)
        tz = ZoneInfo(timezone_id)
        now_local = datetime.now(tz)

        line = (await session.execute(select(FeedingLineModel).order_by(FeedingLineModel.name))).scalars().first()
        if line is None:
            raise RuntimeError(
                "No hay feeding_lines. Crea/sincroniza el trazado del sistema antes de ejecutar el seed."
            )

        targets = await _build_targets(session, line.id)
        if not targets:
            raise RuntimeError(
                "No hay jaulas disponibles para alimentar. Crea jaulas/asignaciones antes de ejecutar el seed."
            )

        doser = (
            await session.execute(
                select(DoserModel).where(DoserModel.line_id == line.id).order_by(DoserModel.name)
            )
        ).scalars().first()
        silo_id = doser.silo_id if doser and doser.silo_id else await _get_first_silo_id(session)

        await _clear_previous_seed_data(session)

        sessions_created = 0
        cage_feedings_created = 0
        events_created = 0

        for day in _current_week_dates(now_local):
            for session_number, start_time in enumerate((time(8, 15), time(11, 30), time(15, 45)), start=1):
                start_local = datetime.combine(day, start_time, tzinfo=tz)
                if start_local >= now_local - timedelta(minutes=10):
                    continue

                selected_targets = _select_targets(targets, session_number)
                session_models, cage_feeding_models, event_models = _make_completed_session(
                    line_id=line.id,
                    doser_id=doser.id if doser else None,
                    silo_id=silo_id,
                    targets=selected_targets,
                    session_number=session_number,
                    start_local=start_local,
                )

                session.add(session_models)
                session.add_all(cage_feeding_models)
                session.add_all(event_models)
                sessions_created += 1
                cage_feedings_created += len(cage_feeding_models)
                events_created += len(event_models)

        await session.commit()

    await close_db_connection()
    print(
        "Seed completado: "
        f"{sessions_created} sesiones, "
        f"{cage_feedings_created} alimentaciones de jaula, "
        f"{events_created} eventos. "
        f"operator_id={SEED_OPERATOR_ID}"
    )


async def _get_timezone_id(session) -> str:
    config = (await session.execute(select(SystemConfigModel).where(SystemConfigModel.id == 1))).scalars().first()
    return config.timezone_id if config else "America/Santiago"


async def _build_targets(session, line_id: UUID) -> list[FeedingTarget]:
    assignments = (
        await session.execute(
            select(SlotAssignmentModel)
            .where(SlotAssignmentModel.line_id == line_id)
            .order_by(SlotAssignmentModel.slot_number)
        )
    ).scalars().all()

    if assignments:
        cage_ids = [assignment.cage_id for assignment in assignments]
        cages = (await session.execute(select(CageModel).where(CageModel.id.in_(cage_ids)))).scalars().all()
        cages_by_id = {cage.id: cage for cage in cages}
        return [
            _target_from_cage(cages_by_id[assignment.cage_id], assignment.slot_number)
            for assignment in assignments
            if assignment.cage_id in cages_by_id
        ]

    cages = (await session.execute(select(CageModel).order_by(CageModel.name).limit(6))).scalars().all()
    return [_target_from_cage(cage, index) for index, cage in enumerate(cages, start=1)]


async def _get_first_silo_id(session) -> UUID | None:
    silo = (await session.execute(select(SiloModel).order_by(SiloModel.name))).scalars().first()
    return silo.id if silo else None


async def _clear_previous_seed_data(session) -> None:
    seeded_session_ids = (
        await session.execute(select(FeedingSessionModel.id).where(FeedingSessionModel.operator_id == SEED_OPERATOR_ID))
    ).scalars().all()

    if not seeded_session_ids:
        return

    await session.execute(delete(FeedingEventModel).where(FeedingEventModel.feeding_session_id.in_(seeded_session_ids)))
    await session.execute(delete(CageFeedingModel).where(CageFeedingModel.feeding_session_id.in_(seeded_session_ids)))
    await session.execute(delete(FeedingSessionModel).where(FeedingSessionModel.id.in_(seeded_session_ids)))


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


def _current_week_dates(now_local: datetime) -> list[datetime.date]:
    week_start = now_local.date() - timedelta(days=now_local.weekday())
    return [week_start + timedelta(days=offset) for offset in range(now_local.weekday() + 1)]


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
) -> tuple[FeedingSessionModel, list[CageFeedingModel], list[FeedingEventModel]]:
    session_id = str(uuid4())
    start_utc = start_local.astimezone(timezone.utc)
    cursor = start_utc

    cage_feedings: list[CageFeedingModel] = []
    events: list[FeedingEventModel] = [
        _event(session_id, "session_started", cursor, {"operator_id": SEED_OPERATOR_ID, "seed": True})
    ]

    total_programmed = 0.0
    total_dispensed = 0.0

    for order, target in enumerate(targets, start=1):
        programmed_kg = round(target.programmed_kg * random.uniform(0.9, 1.15), 2)
        dispensed_kg = round(programmed_kg * random.uniform(0.94, 1.03), 2)
        visits = target.visits
        visit_kg = dispensed_kg / visits
        visit_duration_seconds = max(45.0, (visit_kg / target.rate_kg_per_min) * 60)

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
            cursor += timedelta(seconds=random.randint(25, 70))
            events.append(
                _event(
                    session_id,
                    "visit_started",
                    cursor,
                    {
                        "cage_id": str(target.cage_id),
                        "visit_number": visit_number,
                        "cycle_number": visit_number,
                        "is_empty_visit": False,
                    },
                )
            )
            cursor += timedelta(seconds=visit_duration_seconds * random.uniform(0.92, 1.14))
            events.append(
                _event(
                    session_id,
                    "visit_completed",
                    cursor,
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

        total_programmed += programmed_kg
        total_dispensed += dispensed_kg

    if session_number == 2 and targets:
        changed_target = targets[0]
        events.append(
            _event(
                session_id,
                "rate_changed",
                start_utc + timedelta(minutes=8),
                {
                    "cage_id": str(changed_target.cage_id),
                    "previous_rate": changed_target.rate_kg_per_min,
                    "new_rate": round(changed_target.rate_kg_per_min * 1.08, 2),
                    "applied_immediately": True,
                },
            )
        )

    end_utc = cursor + timedelta(seconds=random.randint(60, 180))
    duration_seconds = (end_utc - start_utc).total_seconds()
    events.append(
        _event(
            session_id,
            "session_completed",
            end_utc,
            {
                "total_dispensed_kg": round(total_dispensed, 2),
                "duration_seconds": round(duration_seconds, 2),
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
