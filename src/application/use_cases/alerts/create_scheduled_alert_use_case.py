"""Caso de uso para crear una alerta programada."""

from application.dtos.alert_dtos import CreateScheduledAlertRequest, ScheduledAlertDTO
from domain.aggregates.scheduled_alert import ScheduledAlert
from domain.enums import AlertCategory, AlertType, ScheduledAlertFrequency
from domain.repositories import IScheduledAlertRepository


class CreateScheduledAlertUseCase:
    """Caso de uso para crear una alerta programada."""

    def __init__(self, scheduled_alert_repository: IScheduledAlertRepository):
        self._repo = scheduled_alert_repository

    async def execute(self, request: CreateScheduledAlertRequest) -> ScheduledAlertDTO:
        """
        Crea una nueva alerta programada.

        Args:
            request: Datos de la alerta programada.

        Returns:
            Alerta programada creada.

        Raises:
            ValueError: Si los datos son inválidos.
        """
        # Validar y convertir enums
        try:
            alert_type = AlertType(request.type)
            category = AlertCategory(request.category)
            frequency = ScheduledAlertFrequency(request.frequency)
        except ValueError as e:
            raise ValueError(f"Valor de enum inválido: {e}")

        # Crear aggregate
        scheduled_alert = ScheduledAlert(
            title=request.title,
            message=request.message,
            type=alert_type,
            category=category,
            frequency=frequency,
            next_trigger_date=request.next_trigger_date,
            days_before_warning=request.days_before_warning,
            device_id=request.device_id,
            device_name=request.device_name,
            custom_days_interval=request.custom_days_interval,
            metadata=request.metadata,
        )

        # Guardar
        await self._repo.save(scheduled_alert)

        return ScheduledAlertDTO(
            id=str(scheduled_alert.id),
            title=scheduled_alert.title,
            message=scheduled_alert.message,
            type=scheduled_alert.type.value,
            category=scheduled_alert.category.value,
            frequency=scheduled_alert.frequency.value,
            next_trigger_date=scheduled_alert.next_trigger_date,
            days_before_warning=scheduled_alert.days_before_warning,
            is_active=scheduled_alert.is_active,
            device_id=scheduled_alert.device_id,
            device_name=scheduled_alert.device_name,
            custom_days_interval=scheduled_alert.custom_days_interval,
            metadata=scheduled_alert.metadata,
            created_at=scheduled_alert.created_at,
            last_triggered_at=scheduled_alert.last_triggered_at,
        )
