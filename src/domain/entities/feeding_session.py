import uuid
from datetime import datetime, timezone
from typing import List, Optional
from enum import Enum


class FeedingType(Enum):
    """Tipos de sesión de alimentación."""
    MANUAL = "MANUAL"
    CYCLIC = "CYCLIC"
    SCHEDULED = "SCHEDULED"


class SessionStatus(Enum):
    """Estados de una sesión de alimentación."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    INTERRUPTED = "INTERRUPTED"


class FeedingSession:
    def __init__(
        self,
        feeding_type: FeedingType,
        line_id: str,
        operator_id: str,
        total_programmed_kg: float,
        allow_overtime: bool = False,
        scheduled_start: Optional[datetime] = None,
    ):
        self._id = str(uuid.uuid4())
        self._line_id = line_id

        if not isinstance(feeding_type, FeedingType):
            raise ValueError("El tipo de alimentación debe ser MANUAL, CYCLIC o SCHEDULED")
        self._type = feeding_type

        self._operator_id = operator_id
        self._allow_overtime = allow_overtime

        if total_programmed_kg <= 0:
            raise ValueError("La cantidad total programada debe ser mayor a 0")
        self._total_programmed_kg = total_programmed_kg

        self._scheduled_start = scheduled_start
        self._actual_start: Optional[datetime] = None
        self._actual_end: Optional[datetime] = None

        self._status = SessionStatus.PENDING
        self._cage_feedings: List = []
        self._events: List = []

    @property
    def id(self):
        return self._id

    @property
    def line_id(self):
        return self._line_id

    @property
    def type(self):
        return self._type

    @property
    def operator_id(self):
        return self._operator_id

    @property
    def allow_overtime(self):
        return self._allow_overtime

    @property
    def total_programmed_kg(self):
        return self._total_programmed_kg

    @property
    def scheduled_start(self):
        return self._scheduled_start

    @property
    def actual_start(self):
        return self._actual_start

    @property
    def actual_end(self):
        return self._actual_end

    @property
    def status(self):
        return self._status

    @property
    def cage_feedings(self):
        return list(self._cage_feedings)

    @property
    def events(self):
        return list(self._events)

    @property
    def total_dispensed_kg(self):
        return sum(cf.dispensed_kg for cf in self._cage_feedings)

    def add_cage_feeding(self, cage_feeding):
        self._cage_feedings.append(cage_feeding)

    def add_event(self, event):
        self._events.append(event)

    def start(self):
        if self._status != SessionStatus.PENDING:
            raise ValueError(f"No se puede iniciar una sesión en estado {self._status.value}")
        self._status = SessionStatus.IN_PROGRESS
        self._actual_start = datetime.now(timezone.utc)

    def pause(self):
        if self._status != SessionStatus.IN_PROGRESS:
            raise ValueError(f"No se puede pausar una sesión en estado {self._status.value}")
        self._status = SessionStatus.PAUSED

    def resume(self):
        if self._status != SessionStatus.PAUSED:
            raise ValueError(f"No se puede reanudar una sesión en estado {self._status.value}")
        self._status = SessionStatus.IN_PROGRESS

    def complete(self):
        if self._status not in [SessionStatus.IN_PROGRESS, SessionStatus.PAUSED]:
            raise ValueError(f"No se puede completar una sesión en estado {self._status.value}")
        self._status = SessionStatus.COMPLETED
        self._actual_end = datetime.now(timezone.utc)

    def cancel(self):
        if self._status in [SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.INTERRUPTED]:
            raise ValueError(f"No se puede cancelar una sesión en estado {self._status.value}")
        self._status = SessionStatus.CANCELLED
        self._actual_end = datetime.now(timezone.utc)

    def interrupt(self):
        if self._status not in [SessionStatus.IN_PROGRESS, SessionStatus.PAUSED]:
            raise ValueError(f"No se puede interrumpir una sesión en estado {self._status.value}")
        self._status = SessionStatus.INTERRUPTED
        self._actual_end = datetime.now(timezone.utc)
