"""Caso de uso para actualizar una alerta."""

from application.dtos.alert_dtos import AlertDTO, UpdateAlertRequest
from domain.enums import AlertStatus
from domain.repositories import IAlertRepository
from domain.value_objects import AlertId


class UpdateAlertUseCase:
    """Caso de uso para actualizar una alerta."""

    def __init__(self, alert_repository: IAlertRepository):
        self._alert_repo = alert_repository

    async def execute(self, alert_id: str, request: UpdateAlertRequest) -> AlertDTO:
        """
        Actualiza una alerta existente.

        Args:
            alert_id: ID de la alerta a actualizar.
            request: Datos a actualizar (status, resolved_by).

        Returns:
            Alerta actualizada.

        Raises:
            ValueError: Si la alerta no existe.
        """
        # Buscar alerta
        alert = await self._alert_repo.find_by_id(AlertId.from_string(alert_id))
        if not alert:
            raise ValueError(f"Alerta {alert_id} no encontrada")

        # Actualizar campos
        if request.status:
            new_status = AlertStatus(request.status)
            if new_status == AlertStatus.RESOLVED:
                alert.resolve(resolved_by=request.resolved_by)
            elif new_status == AlertStatus.ARCHIVED:
                alert.archive()
            else:
                alert.update_status(new_status)
        elif request.resolved_by and alert.status == AlertStatus.RESOLVED:
            # Solo actualizar resolved_by si ya está resuelto
            alert._resolved_by = request.resolved_by

        # Guardar
        await self._alert_repo.save(alert)

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
            metadata=alert.metadata,
        )
