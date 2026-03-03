"""Caso de uso para contar alertas silenciadas."""

from application.dtos.alert_dtos import SnoozedCountResponse
from domain.repositories import IAlertRepository
from domain.value_objects import UserId


class GetSnoozedCountUseCase:
    """Caso de uso para obtener el contador de alertas silenciadas."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, user_id: UserId) -> SnoozedCountResponse:
        """
        Obtiene el total de alertas actualmente silenciadas.

        Args:
            user_id: ID del usuario propietario.

        Returns:
            SnoozedCountResponse con el contador
        """
        count = await self._alert_repo.count_snoozed(user_id=user_id)
        return SnoozedCountResponse(count=count)
