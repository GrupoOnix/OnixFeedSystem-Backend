"""Caso de uso para actualizar una alerta programada."""

from application.dtos.alert_dtos import ScheduledAlertDTO, UpdateScheduledAlertRequest
from domain.enums import AlertCategory, AlertType, ScheduledAlertFrequency
from domain.repositories import IScheduledAlertRepository
from domain.value_objects import ScheduledAlertId


class UpdateScheduledAlertUseCase:
    """Caso de uso para actualizar una alerta programada."""

    def __init__(self, scheduled_alert_repository: IScheduledAlertRepository):
        self._repo = scheduled_alert_repository

    async def execute(
        self, alert_id: str, request: UpdateScheduledAlertRequest
    ) -> ScheduledAlertDTO:
        """
        Actualiza una alerta programada existente.

        Args:
            alert_id: ID de la alerta programada.
            request: Datos a actualizar.

        Returns:
            Alerta programada actualizada.

        Raises:
            ValueError: Si la alerta no existe o los datos son inválidos.
        """
        # Buscar alerta
        scheduled_alert = await self._repo.find_by_id(
            ScheduledAlertId.from_string(alert_id)
        )
        if not scheduled_alert:
            raise ValueError(f"Alerta programada {alert_id} no encontrada")

        # Convertir enums si están presentes
        alert_type = None
        if request.type:
            alert_type = AlertType(request.type)

        category = None
        if request.category:
            category = AlertCategory(request.category)

        frequency = None
        if request.frequency:
            frequency = ScheduledAlertFrequency(request.frequency)

        # Actualizar
        scheduled_alert.update(
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
