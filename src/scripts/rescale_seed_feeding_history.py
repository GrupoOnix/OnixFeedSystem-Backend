"""Rescale seeded feeding history amounts while keeping events coherent.

Run a dry-run from the repository root:
    python src/scripts/rescale_seed_feeding_history.py

Apply changes:
    python src/scripts/rescale_seed_feeding_history.py --apply
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel import col

SRC_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))
load_dotenv(REPO_ROOT / ".env")

from infrastructure.persistence.database import async_session_maker, close_db_connection  # noqa: E402
from infrastructure.persistence.models.feeding_event_model import FeedingEventModel  # noqa: E402
from infrastructure.persistence.models.feeding_session_model import FeedingSessionModel  # noqa: E402
from infrastructure.persistence.models.system_config_model import SystemConfigModel  # noqa: E402

SEED_OPERATOR_ID = "00000000-0000-0000-0000-00000000feed"
RANDOM_SEED = 20260522
MORNING_TARGET_KG = (120.0, 220.0)
MIDDAY_TARGET_KG = (180.0, 360.0)


@dataclass
class RescaleStats:
    sessions_seen: int = 0
    sessions_changed: int = 0
    sessions_skipped_empty: int = 0
    cage_feedings_changed: int = 0
    visit_events_changed: int = 0
    rate_events_changed: int = 0
    before_total_kg: float = 0.0
    after_total_kg: float = 0.0


async def main() -> None:
    args = _parse_args()

    async with async_session_maker() as session:
        timezone_id = await _get_timezone_id(session)
        tz = ZoneInfo(timezone_id)

        sessions = (
            await session.execute(
                select(FeedingSessionModel)
                .where(col(FeedingSessionModel.operator_id) == SEED_OPERATOR_ID)
                .options(
                    selectinload(cast(Any, FeedingSessionModel.cage_feedings)),
                    selectinload(cast(Any, FeedingSessionModel.events)),
                )
                .order_by(col(FeedingSessionModel.actual_start))
            )
        ).scalars().all()

        stats = RescaleStats(sessions_seen=len(sessions))
        for feeding_session in sessions:
            _rescale_session(feeding_session, tz, stats)

        if args.apply:
            await session.commit()
        else:
            await session.rollback()

    await close_db_connection()
    mode = "APLICADO" if args.apply else "DRY-RUN"
    print(
        f"{mode}: "
        f"{stats.sessions_seen} sesiones revisadas, "
        f"{stats.sessions_changed} sesiones ajustadas, "
        f"{stats.sessions_skipped_empty} sesiones omitidas sin kg, "
        f"{stats.cage_feedings_changed} cage_feedings ajustados, "
        f"{stats.visit_events_changed} visitas ajustadas, "
        f"{stats.rate_events_changed} cambios de tasa ajustados. "
        f"Total antes={stats.before_total_kg:.2f} kg, "
        f"total despues={stats.after_total_kg:.2f} kg, "
        f"promedio antes={_average(stats.before_total_kg, stats.sessions_changed):.2f} kg/sesion, "
        f"promedio despues={_average(stats.after_total_kg, stats.sessions_changed):.2f} kg/sesion."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persiste los ajustes. Sin este flag solo hace dry-run.",
    )
    return parser.parse_args()


async def _get_timezone_id(session) -> str:
    config = (
        await session.execute(select(SystemConfigModel).where(col(SystemConfigModel.id) == 1))
    ).scalars().first()
    return config.timezone_id if config else "America/Santiago"


def _rescale_session(feeding_session: FeedingSessionModel, tz: ZoneInfo, stats: RescaleStats) -> None:
    cage_feedings = list(feeding_session.cage_feedings or [])
    current_total = sum(float(cf.dispensed_kg or 0.0) for cf in cage_feedings)
    if current_total <= 0:
        stats.sessions_skipped_empty += 1
        return

    rng = random.Random(f"{RANDOM_SEED}:{feeding_session.id}")
    target_total = _target_total_kg(feeding_session.actual_start, tz, rng)
    scale = target_total / current_total

    stats.before_total_kg += current_total
    stats.after_total_kg += target_total
    stats.sessions_changed += 1

    visit_events_by_cage = _visit_events_by_cage(feeding_session.events or [])
    new_rates_by_cage: dict[str, float] = {}

    for cage_feeding in cage_feedings:
        old_dispensed = float(cage_feeding.dispensed_kg or 0.0)
        old_programmed = float(cage_feeding.programmed_kg or 0.0)
        new_dispensed = round(old_dispensed * scale, 2)
        new_programmed = round(max(new_dispensed, old_programmed * scale), 2)

        cage_feeding.dispensed_kg = new_dispensed
        cage_feeding.programmed_kg = new_programmed

        cage_id = str(cage_feeding.cage_id)
        visit_events = visit_events_by_cage.get(cage_id, [])
        visit_duration_minutes = _rescale_visit_events(visit_events, old_dispensed, new_dispensed)
        if visit_duration_minutes > 0:
            cage_feeding.rate_kg_per_min = round(new_dispensed / visit_duration_minutes, 2)
        else:
            cage_feeding.rate_kg_per_min = round(float(cage_feeding.rate_kg_per_min or 0.0) * scale, 2)

        new_rates_by_cage[cage_id] = cage_feeding.rate_kg_per_min
        stats.cage_feedings_changed += 1
        stats.visit_events_changed += len(visit_events)

    _rescale_session_events(feeding_session.events or [], target_total, scale, new_rates_by_cage, stats)
    feeding_session.total_programmed_kg = round(sum(float(cf.programmed_kg or 0.0) for cf in cage_feedings), 2)


def _target_total_kg(started_at: datetime | None, tz: ZoneInfo, rng: random.Random) -> float:
    if started_at is None:
        return round(rng.uniform(*MIDDAY_TARGET_KG), 2)

    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    local_hour = started_at.astimezone(tz).hour
    target_range = MORNING_TARGET_KG if local_hour < 10 else MIDDAY_TARGET_KG
    return round(rng.uniform(*target_range), 2)


def _visit_events_by_cage(events: list[FeedingEventModel]) -> dict[str, list[FeedingEventModel]]:
    result: dict[str, list[FeedingEventModel]] = {}
    for event in events:
        if event.event_type != "visit_completed" or not event.data:
            continue

        cage_id = event.data.get("cage_id")
        if cage_id:
            result.setdefault(str(cage_id), []).append(event)

    return result


def _rescale_visit_events(
    visit_events: list[FeedingEventModel],
    old_dispensed_kg: float,
    new_dispensed_kg: float,
) -> float:
    if not visit_events:
        return 0.0

    old_total_grams = sum(float(event.data.get("dispensed_grams") or 0.0) for event in visit_events)
    target_total_grams = new_dispensed_kg * 1000.0
    duration_seconds = 0.0

    for index, event in enumerate(visit_events):
        data = dict(event.data or {})
        if old_total_grams > 0:
            share = float(data.get("dispensed_grams") or 0.0) / old_total_grams
        else:
            share = 1.0 / len(visit_events)

        if index == len(visit_events) - 1:
            previous = sum(float(other.data.get("dispensed_grams") or 0.0) for other in visit_events[:-1])
            dispensed_grams = round(target_total_grams - previous, 2)
        else:
            dispensed_grams = round(target_total_grams * share, 2)

        data["dispensed_grams"] = max(0.0, dispensed_grams)
        data["dispensed_kg"] = round(data["dispensed_grams"] / 1000.0, 3)
        event.data = data
        duration_seconds += float(data.get("duration_seconds") or 0.0)

    if old_dispensed_kg <= 0:
        return duration_seconds / 60.0
    return duration_seconds / 60.0


def _rescale_session_events(
    events: list[FeedingEventModel],
    target_total_kg: float,
    scale: float,
    new_rates_by_cage: dict[str, float],
    stats: RescaleStats,
) -> None:
    for event in events:
        data = dict(event.data or {})

        if event.event_type == "session_completed":
            data["total_dispensed_kg"] = round(target_total_kg, 2)
            data["completion_reason"] = "natural"
            data["completed_by"] = "system"
            event.data = data
            continue

        if event.event_type != "rate_changed":
            continue

        cage_id = str(data.get("cage_id") or "")
        rate = new_rates_by_cage.get(cage_id)
        if rate is None:
            data["previous_rate"] = round(float(data.get("previous_rate") or 0.0) * scale, 2)
            data["new_rate"] = round(float(data.get("new_rate") or 0.0) * scale, 2)
        else:
            previous_rate = float(data.get("previous_rate") or rate)
            direction = 1.0 if float(data.get("new_rate") or previous_rate) >= previous_rate else -1.0
            data["previous_rate"] = round(rate * random.uniform(0.85, 1.0), 2)
            data["new_rate"] = round(max(0.5, rate * (1.0 + direction * random.uniform(0.03, 0.18))), 2)
        event.data = data
        stats.rate_events_changed += 1


def _average(total: float, count: int) -> float:
    return total / count if count else 0.0


if __name__ == "__main__":
    asyncio.run(main())
