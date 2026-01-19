"""Caso de uso para obtener el contador de alertas no leídas."""

from application.dtos.alert_dtos import UnreadCountResponse
from domain.repositories import IAlertRepository


class GetUnreadCountUseCase:
    """Caso de uso para obtener el contador de alertas no leídas."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self) -> UnreadCountResponse:
        """
        Obtiene el contador de alertas no leídas.
        Usado principalmente para el badge en el navbar del frontend.

        Returns:
            Contador de alertas UNREAD.
        """
        count = await self._alert_repo.count_unread()
        return UnreadCountResponse(count=count)
