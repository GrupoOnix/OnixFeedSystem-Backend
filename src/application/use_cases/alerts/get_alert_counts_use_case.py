"""Caso de uso para obtener contadores de alertas por tipo."""

from application.dtos.alert_dtos import AlertCountsResponse
from domain.enums import AlertType
from domain.repositories import IAlertRepository
from domain.value_objects import UserId


class GetAlertCountsUseCase:
    """Caso de uso para obtener contadores de alertas activas por tipo."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, user_id: UserId) -> AlertCountsResponse:
        """
        Obtiene los contadores de alertas activas por tipo.

        Excluye alertas resueltas y alertas silenciadas.

        Args:
            user_id: ID del usuario propietario.

        Returns:
            AlertCountsResponse con contadores por tipo
        """
        critical_count = await self._alert_repo.count_by_type(
            type=AlertType.CRITICAL,
            user_id=user_id,
            exclude_resolved=True,
            exclude_snoozed=True,
        )

        warning_count = await self._alert_repo.count_by_type(
            type=AlertType.WARNING,
            user_id=user_id,
            exclude_resolved=True,
            exclude_snoozed=True,
        )

        info_count = await self._alert_repo.count_by_type(
            type=AlertType.INFO,
            user_id=user_id,
            exclude_resolved=True,
            exclude_snoozed=True,
        )

        success_count = await self._alert_repo.count_by_type(
            type=AlertType.SUCCESS,
            user_id=user_id,
            exclude_resolved=True,
            exclude_snoozed=True,
        )

        return AlertCountsResponse(
            critical=critical_count,
            warning=warning_count,
            info=info_count,
            success=success_count,
        )
