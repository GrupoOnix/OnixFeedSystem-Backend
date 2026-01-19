"""Caso de uso para eliminar una alerta programada."""

from domain.repositories import IScheduledAlertRepository
from domain.value_objects import ScheduledAlertId


class DeleteScheduledAlertUseCase:
    """Caso de uso para eliminar una alerta programada."""

    def __init__(self, scheduled_alert_repository: IScheduledAlertRepository):
        self._repo = scheduled_alert_repository

    async def execute(self, alert_id: str) -> None:
        """
        Elimina una alerta programada.

        Args:
            alert_id: ID de la alerta programada a eliminar.

        Raises:
            ValueError: Si la alerta no existe.
        """
        scheduled_alert_id = ScheduledAlertId.from_string(alert_id)

        # Verificar que existe
        existing = await self._repo.find_by_id(scheduled_alert_id)
        if not existing:
            raise ValueError(f"Alerta programada {alert_id} no encontrada")

        await self._repo.delete(scheduled_alert_id)
