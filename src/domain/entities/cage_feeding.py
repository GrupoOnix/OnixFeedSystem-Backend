import uuid
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class CageFeedingMode(Enum):
    """Modos de alimentación de una jaula."""
    NORMAL = "NORMAL"
    PAUSE = "PAUSE"
    FASTING = "FASTING"


class CageFeedingStatus(Enum):
    """Estados de alimentación de una jaula."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CageFeeding:

    def __init__(
        self,
        feeding_session_id: str,
        cage_id: str,
        doser_id: str,
        silo_id: str,
        execution_order: int,
        programmed_kg: float,
        programmed_visits: int,
        rate_kg_per_min: float,
        mode: CageFeedingMode = CageFeedingMode.NORMAL,
    ):
        self._id = str(uuid.uuid4())
        self._feeding_session_id = feeding_session_id
        self._cage_id = cage_id
        self._doser_id = doser_id
        self._silo_id = silo_id
        self._mode = mode
        self._rate_kg_per_min = rate_kg_per_min
        self._status = CageFeedingStatus.PENDING

        if execution_order <= 0:
            raise ValueError("El orden de ejecución debe ser mayor a 0")
        self._execution_order = execution_order

        if programmed_kg <= 0:
            raise ValueError("La cantidad programada debe ser mayor a 0")
        self._programmed_kg = programmed_kg

        if programmed_visits <= 0:
            raise ValueError("Las visitas programadas deben ser mayor a 0")
        self._programmed_visits = programmed_visits

        self._dispensed_kg: float = 0.0
        self._completed_visits: int = 0

    @property
    def id(self):
        return self._id

    @property
    def feeding_session_id(self):
        return self._feeding_session_id

    @property
    def cage_id(self):
        return self._cage_id

    @property
    def doser_id(self):
        return self._doser_id

    @property
    def silo_id(self):
        return self._silo_id

    @property
    def execution_order(self):
        return self._execution_order

    @property
    def programmed_kg(self):
        return self._programmed_kg

    @property
    def dispensed_kg(self):
        return self._dispensed_kg

    @property
    def programmed_visits(self):
        return self._programmed_visits

    @property
    def completed_visits(self):
        return self._completed_visits

    @property
    def status(self):
        return self._status

    @property
    def mode(self):
        return self._mode

    @property
    def rate_kg_per_min(self):
        return self._rate_kg_per_min

    def set_mode(self, mode: CageFeedingMode):
        if not isinstance(mode, CageFeedingMode):
            raise ValueError("El modo debe ser una instancia de CageFeedingMode")
        self._mode = mode

    def set_rate(self, rate_kg_per_min: float):
        if rate_kg_per_min <= 0:
            raise ValueError("La tasa debe ser mayor a 0")
        self._rate_kg_per_min = rate_kg_per_min

    def start(self):
        if self._status != CageFeedingStatus.PENDING:
            raise ValueError(f"No se puede iniciar una alimentación en estado {self._status.value}")
        self._status = CageFeedingStatus.IN_PROGRESS

    def complete(self):
        if self._status != CageFeedingStatus.IN_PROGRESS:
            raise ValueError(f"No se puede completar una alimentación en estado {self._status.value}")
        self._status = CageFeedingStatus.COMPLETED

    def cancel(self):
        if self._status in [CageFeedingStatus.COMPLETED, CageFeedingStatus.CANCELLED]:
            raise ValueError(f"No se puede cancelar una alimentación en estado {self._status.value}")
        self._status = CageFeedingStatus.CANCELLED

    def add_dispensed_amount(self, kg: float) -> None:
        if kg < 0:
            raise ValueError("La cantidad dispensada no puede ser negativa")
        self._dispensed_kg += kg

    def increment_completed_visits(self) -> None:
        if self._completed_visits < self._programmed_visits:
            self._completed_visits += 1

    def completion_percentage(self) -> float:
        if self._programmed_kg == 0:
            return 0.0
        return (self._dispensed_kg / self._programmed_kg) * 100.0

    def visits_completion_percentage(self) -> float:
        if self._programmed_visits == 0:
            return 0.0
        return (self._completed_visits / self._programmed_visits) * 100.0
