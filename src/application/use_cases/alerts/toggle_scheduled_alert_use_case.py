"""Caso de uso para activar/desactivar una alerta programada."""

from application.dtos.alert_dtos import ToggleScheduledAlertResponse
from domain.repositories import IScheduledAlertRepository
from domain.value_objects import ScheduledAlertId


class ToggleScheduledAlertUseCase:
    """Caso de uso para activar/desactivar una alerta programada."""

    def __init__(self, scheduled_alert_repository: IScheduledAlertRepository):
        self._repo = scheduled_alert_repository

    async def execute(self, alert_id: str) -> ToggleScheduledAlertResponse:
        """
        Activa/desactiva una alerta programada.

        Args:
            alert_id: ID de la alerta programada.

        Returns:
            Nuevo estado de is_active.

        Raises:
            ValueError: Si la alerta no existe.
        """
        scheduled_alert = await self._repo.find_by_id(
            ScheduledAlertId.from_string(alert_id)
        )
        if not scheduled_alert:
            raise ValueError(f"Alerta programada {alert_id} no encontrada")

        # Toggle
        new_state = scheduled_alert.toggle_active()

        # Guardar
        await self._repo.save(scheduled_alert)

        return ToggleScheduledAlertResponse(is_active=new_state)
