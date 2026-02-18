
from datetime import datetime, time
from zoneinfo import ZoneInfo


class SystemConfig:

    _SINGLETON_ID: int = 1

    def __init__(
        self,
        feeding_start_time: time,
        feeding_end_time: time,
        timezone_id: str,
    ) -> None:
        self._id = self._SINGLETON_ID
        self._feeding_start_time = feeding_start_time
        self._feeding_end_time = feeding_end_time
        self._timezone_id = timezone_id


    @property
    def id(self) -> int:
        return self._id

    @property
    def feeding_start_time(self) -> time:
        return self._feeding_start_time

    @property
    def feeding_end_time(self) -> time:
        return self._feeding_end_time

    @property
    def timezone_id(self) -> str:
        return self._timezone_id


    def seconds_remaining_in_window(self, now_utc: datetime) -> float:
        """
        Calcula los segundos que quedan dentro del horario operativo
        a partir de un instante UTC dado.

        Si now_utc está fuera del horario operativo (antes del inicio o
        después del fin), retorna 0.0.

        Args:
            now_utc: Instante actual en UTC (timezone-aware).

        Returns:
            Segundos restantes hasta feeding_end_time en la zona local.
        """
        tz = ZoneInfo(self._timezone_id)
        now_local = now_utc.astimezone(tz)
        today = now_local.date()

        window_end = datetime.combine(today, self._feeding_end_time, tzinfo=tz)
        window_start = datetime.combine(today, self._feeding_start_time, tzinfo=tz)

        if now_local < window_start or now_local >= window_end:
            return 0.0

        return (window_end - now_local).total_seconds()

    def is_within_window(self, now_utc: datetime) -> bool:
        """Retorna True si now_utc cae dentro del horario operativo."""
        return self.seconds_remaining_in_window(now_utc) > 0.0


    def update(
        self,
        feeding_start_time: time,
        feeding_end_time: time,
        timezone_id: str,
    ) -> None:
        if feeding_end_time <= feeding_start_time:
            raise ValueError(
                "feeding_end_time debe ser posterior a feeding_start_time"
            )
        self._feeding_start_time = feeding_start_time
        self._feeding_end_time = feeding_end_time
        self._timezone_id = timezone_id


    @classmethod
    def create_default(cls) -> "SystemConfig":
        """Crea una configuración por defecto: 06:00–18:00 America/Santiago."""
        return cls(
            feeding_start_time=time(6, 0),
            feeding_end_time=time(18, 0),
            timezone_id="America/Santiago",
        )
