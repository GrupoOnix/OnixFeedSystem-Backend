"""Caso de uso para marcar una alerta como leída."""

from domain.repositories import IAlertRepository
from domain.value_objects import AlertId


class MarkAlertReadUseCase:
    """Caso de uso para marcar una alerta como leída."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, alert_id: str) -> None:
        """
        Marca una alerta como leída.

        Args:
            alert_id: ID de la alerta a marcar.

        Raises:
            ValueError: Si la alerta no existe.
        """
        alert = await self._alert_repo.find_by_id(AlertId.from_string(alert_id))
        if not alert:
            raise ValueError(f"Alerta {alert_id} no encontrada")

        alert.mark_as_read()
        await self._alert_repo.save(alert)
