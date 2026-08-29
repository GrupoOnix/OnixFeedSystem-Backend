"""Política temporal para disparar planes diarios sin depender de un minuto exacto."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum


class ScheduledFeedingWindowStatus(str, Enum):
    NOT_DUE = "NOT_DUE"
    DUE = "DUE"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class ScheduledFeedingWindow:
    status: ScheduledFeedingWindowStatus
    scheduled_at: datetime
    expires_at: datetime


def evaluate_scheduled_feeding_window(
    start_time: str,
    now: datetime,
    grace_period: timedelta,
) -> ScheduledFeedingWindow:
    """Evalúa la ventana local de un plan para la fecha de ``now``."""
    if now.tzinfo is None:
        raise ValueError("now debe incluir zona horaria")
    if grace_period <= timedelta(0):
        raise ValueError("grace_period debe ser mayor que cero")

    scheduled_time = time.fromisoformat(start_time)
    scheduled_at = datetime.combine(now.date(), scheduled_time, tzinfo=now.tzinfo)
    expires_at = scheduled_at + grace_period
    if now < scheduled_at:
        status = ScheduledFeedingWindowStatus.NOT_DUE
    elif now < expires_at:
        status = ScheduledFeedingWindowStatus.DUE
    else:
        status = ScheduledFeedingWindowStatus.EXPIRED
    return ScheduledFeedingWindow(status=status, scheduled_at=scheduled_at, expires_at=expires_at)
