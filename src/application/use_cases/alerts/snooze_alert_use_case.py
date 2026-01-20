"""Caso de uso para silenciar una alerta temporalmente."""

from domain.repositories import IAlertRepository
from domain.value_objects import AlertId


class SnoozeAlertUseCase:
    """Caso de uso para silenciar una alerta temporalmente."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, alert_id: str, duration_days: int) -> None:
        """
        Silencia una alerta por un período específico.

        Args:
            alert_id: ID de la alerta a silenciar.
            duration_days: Duración del silenciamiento en días (1 o 7).

        Raises:
            ValueError: Si la alerta no existe o la duración es inválida.
        """
        if duration_days not in [1, 7]:
            raise ValueError("La duración debe ser 1 o 7 días")

        alert = await self._alert_repo.find_by_id(AlertId.from_string(alert_id))
        if not alert:
            raise ValueError(f"Alerta {alert_id} no encontrada")

        alert.snooze(duration_days)
        await self._alert_repo.save(alert)
