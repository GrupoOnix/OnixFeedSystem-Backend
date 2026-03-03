"""Caso de uso para obtener el contador de alertas no leídas."""

from application.dtos.alert_dtos import UnreadCountResponse
from domain.repositories import IAlertRepository
from domain.value_objects import UserId


class GetUnreadCountUseCase:
    """Caso de uso para obtener el contador de alertas no leídas."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, user_id: UserId) -> UnreadCountResponse:
        """
        Obtiene el contador de alertas no leídas.
        Usado principalmente para el badge en el navbar del frontend.

        Args:
            user_id: ID del usuario propietario.

        Returns:
            Contador de alertas UNREAD.
        """
        count = await self._alert_repo.count_unread(user_id=user_id)
        return UnreadCountResponse(count=count)
