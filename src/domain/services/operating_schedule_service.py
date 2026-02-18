
from datetime import datetime, timezone

from domain.aggregates.system_config import SystemConfig


class OperatingScheduleService:
    """
    Verifica si la duración estimada de una sesión de alimentación
    cabe dentro del horario operativo configurado en SystemConfig.

    Regla:
        Si allow_overtime es False, el tiempo estimado de la sesión
        (en segundos) debe ser menor o igual a los segundos que quedan
        en la ventana operativa desde el instante actual.
    """

    def __init__(self, config: SystemConfig) -> None:
        self._config = config

    def fits_in_window(
        self,
        estimated_seconds: float,
        now_utc: datetime | None = None,
    ) -> bool:
        """
        Retorna True si estimated_seconds cabe dentro del tiempo restante.

        Args:
            estimated_seconds: Duración estimada de la sesión (segundos).
            now_utc: Instante de referencia (UTC). Si es None, usa datetime.now(UTC).
        """
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        remaining = self._config.seconds_remaining_in_window(now_utc)
        return estimated_seconds <= remaining

    def assert_fits_in_window(
        self,
        estimated_seconds: float,
        now_utc: datetime | None = None,
    ) -> None:
        """
        Lanza ValueError si estimated_seconds no cabe en el horario.

        Args:
            estimated_seconds: Duración estimada de la sesión (segundos).
            now_utc: Instante de referencia (UTC). Si es None, usa datetime.now(UTC).

        Raises:
            ValueError: Si la sesión excedería el horario operativo.
        """
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)

        remaining = self._config.seconds_remaining_in_window(now_utc)

        if remaining <= 0.0:
            raise ValueError(
                f"Fuera del horario operativo "
                f"({self._config.feeding_start_time.strftime('%H:%M')}–"
                f"{self._config.feeding_end_time.strftime('%H:%M')} "
                f"{self._config.timezone_id}). No se puede iniciar la alimentación."
            )

        if estimated_seconds > remaining:
            remaining_min = remaining / 60
            estimated_min = estimated_seconds / 60
            raise ValueError(
                f"La alimentación estimada ({estimated_min:.1f} min) no cabe en el "
                f"tiempo operativo restante ({remaining_min:.1f} min). "
                f"Use allow_overtime=True para ignorar esta restricción."
            )
