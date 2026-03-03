"""Caso de uso para marcar todas las alertas como leídas."""

from application.dtos.alert_dtos import MarkAllReadResponse
from domain.repositories import IAlertRepository
from domain.value_objects import UserId


class MarkAllAlertsReadUseCase:
    """Caso de uso para marcar todas las alertas como leídas."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, user_id: UserId) -> MarkAllReadResponse:
        """
        Marca todas las alertas UNREAD como READ del usuario.

        Args:
            user_id: ID del usuario propietario.

        Returns:
            Cantidad de alertas actualizadas.
        """
        count = await self._alert_repo.mark_all_as_read(user_id=user_id)
        return MarkAllReadResponse(
            count=count,
            message=f"{count} alertas marcadas como leídas",
        )
