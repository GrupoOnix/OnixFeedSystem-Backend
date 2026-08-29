"""Detección de conflictos entre planes diarios de una misma línea."""

from dataclasses import dataclass
from typing import Iterable


class ScheduledPlanConflictError(ValueError):
    pass


@dataclass(frozen=True)
class DailyInterval:
    start_seconds: int
    end_seconds: int


def daily_interval(start_time: str, end_time: str) -> DailyInterval:
    start_hours, start_minutes = map(int, start_time.split(":"))
    end_hours, end_minutes = map(int, end_time.split(":"))
    start_seconds = start_hours * 3600 + start_minutes * 60
    end_seconds = end_hours * 3600 + end_minutes * 60
    if end_seconds <= start_seconds:
        raise ValueError("La alimentación debe comenzar y terminar durante el mismo día")
    return DailyInterval(start_seconds, end_seconds)


def intervals_overlap(first: DailyInterval, second: DailyInterval) -> bool:
    return max(first.start_seconds, second.start_seconds) < min(first.end_seconds, second.end_seconds)


def assert_no_scheduled_plan_conflict(
    *,
    start_time: str,
    end_time: str,
    timezone: str,
    existing_plans: Iterable[object],
) -> None:
    candidate = daily_interval(start_time, end_time)
    for plan in existing_plans:
        if plan.timezone != timezone:
            raise ScheduledPlanConflictError(
                f"La línea ya tiene un plan activo con zona horaria {plan.timezone}; "
                "todos sus planes activos deben usar la misma zona horaria"
            )
        if intervals_overlap(candidate, daily_interval(plan.start_time, plan.end_time)):
            raise ScheduledPlanConflictError(
                f"El horario se superpone con el plan activo '{plan.name}' de la misma línea"
            )
