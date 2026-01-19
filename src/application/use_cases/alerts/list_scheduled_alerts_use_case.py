"""Caso de uso para listar alertas programadas."""

from typing import List

from application.dtos.alert_dtos import ListScheduledAlertsResponse, ScheduledAlertDTO
from domain.aggregates.scheduled_alert import ScheduledAlert
from domain.repositories import IScheduledAlertRepository


class ListScheduledAlertsUseCase:
    """Caso de uso para listar alertas programadas."""

    def __init__(self, scheduled_alert_repository: IScheduledAlertRepository):
        self._repo = scheduled_alert_repository

    async def execute(self) -> ListScheduledAlertsResponse:
        """
        Lista todas las alertas programadas.

        Returns:
            Lista de alertas programadas ordenadas por próxima fecha de disparo.
        """
        scheduled_alerts = await self._repo.get_all()
        dtos = [self._to_dto(sa) for sa in scheduled_alerts]
        return ListScheduledAlertsResponse(scheduled_alerts=dtos)

    @staticmethod
    def _to_dto(sa: ScheduledAlert) -> ScheduledAlertDTO:
        """Convierte un aggregate ScheduledAlert a DTO."""
        return ScheduledAlertDTO(
            id=str(sa.id),
            title=sa.title,
            message=sa.message,
            type=sa.type.value,
            category=sa.category.value,
            frequency=sa.frequency.value,
            next_trigger_date=sa.next_trigger_date,
            days_before_warning=sa.days_before_warning,
            is_active=sa.is_active,
            device_id=sa.device_id,
            device_name=sa.device_name,
            custom_days_interval=sa.custom_days_interval,
            metadata=sa.metadata,
            created_at=sa.created_at,
            last_triggered_at=sa.last_triggered_at,
        )
