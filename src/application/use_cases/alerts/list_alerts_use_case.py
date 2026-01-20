"""Caso de uso para listar alertas."""

from typing import List

from application.dtos.alert_dtos import AlertDTO, ListAlertsRequest, ListAlertsResponse
from domain.aggregates.alert import Alert
from domain.enums import AlertCategory, AlertStatus, AlertType
from domain.repositories import IAlertRepository


class ListAlertsUseCase:
    """Caso de uso para listar alertas con filtros."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, request: ListAlertsRequest) -> ListAlertsResponse:
        """
        Lista alertas con filtros opcionales.

        Args:
            request: Filtros y paginación.

        Returns:
            Lista de alertas que cumplen los filtros.
        """
        # Convertir strings a enums
        status_list = None
        if request.status:
            status_list = [AlertStatus(s) for s in request.status]

        type_list = None
        if request.type:
            type_list = [AlertType(t) for t in request.type]

        category_list = None
        if request.category:
            category_list = [AlertCategory(c) for c in request.category]

        # Obtener alertas
        alerts = await self._alert_repo.list(
            status=status_list,
            type=type_list,
            category=category_list,
            search=request.search,
            limit=request.limit,
            offset=request.offset,
        )

        # Convertir a DTOs
        alert_dtos = [self._to_dto(alert) for alert in alerts]

        return ListAlertsResponse(alerts=alert_dtos, total=len(alert_dtos))

    @staticmethod
    def _to_dto(alert: Alert) -> AlertDTO:
        """Convierte un aggregate Alert a DTO."""
        return AlertDTO(
            id=str(alert.id),
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
