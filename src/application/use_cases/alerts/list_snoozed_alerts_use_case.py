"""Caso de uso para listar alertas silenciadas."""

from application.dtos.alert_dtos import AlertDTO, ListAlertsResponse
from domain.repositories import IAlertRepository


class ListSnoozedAlertsUseCase:
    """Caso de uso para listar alertas actualmente silenciadas."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, limit: int = 50, offset: int = 0) -> ListAlertsResponse:
        """
        Lista todas las alertas que están actualmente silenciadas.

        Args:
            limit: Cantidad máxima de resultados (default: 50)
            offset: Desplazamiento para paginación (default: 0)

        Returns:
            ListAlertsResponse con alertas silenciadas y total
        """
        alerts, total = await self._alert_repo.list_snoozed(limit=limit, offset=offset)

        # Convertir a DTOs
        alert_dtos = [
            AlertDTO(
                id=str(alert.id.value),
                type=alert.type.value,
                status=alert.status.value,
                category=alert.category.value,
                title=alert.title,
                message=alert.message,
                source=alert.source,
                timestamp=alert.timestamp,
                read_at=alert.read_at,
                resolved_at=alert.resolved_at,
                resolved_by=alert.resolved_by,
                snoozed_until=alert.snoozed_until,
                metadata=alert.metadata,
            )
            for alert in alerts
        ]

        return ListAlertsResponse(alerts=alert_dtos, total=total)
