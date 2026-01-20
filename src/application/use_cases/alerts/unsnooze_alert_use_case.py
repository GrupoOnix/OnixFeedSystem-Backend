"""Caso de uso para reactivar una alerta silenciada."""

from domain.repositories import IAlertRepository
from domain.value_objects import AlertId


class UnsnoozeAlertUseCase:
    """Caso de uso para reactivar (unsnooze) una alerta silenciada."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, alert_id: str) -> None:
        """
        Remueve el silenciamiento de una alerta.

        Args:
            alert_id: ID de la alerta a reactivar.

        Raises:
            ValueError: Si la alerta no existe.
        """
        alert = await self._alert_repo.find_by_id(AlertId.from_string(alert_id))
        if not alert:
            raise ValueError(f"Alerta {alert_id} no encontrada")

        # Remover el snooze (es idempotente, no importa si ya no estaba silenciada)
        alert.unsnooze()
        await self._alert_repo.save(alert)
