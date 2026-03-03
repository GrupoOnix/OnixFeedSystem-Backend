"""Implementación del repositorio de alertas programadas."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.scheduled_alert import ScheduledAlert
from domain.repositories import IScheduledAlertRepository
from domain.value_objects import ScheduledAlertId, UserId
from infrastructure.persistence.models.scheduled_alert_model import ScheduledAlertModel


class ScheduledAlertRepository(IScheduledAlertRepository):
    """Implementación del repositorio de alertas programadas."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, scheduled_alert: ScheduledAlert) -> None:
        """Guarda o actualiza una alerta programada."""
        existing = await self.session.get(ScheduledAlertModel, scheduled_alert.id.value)

        if existing:
            # Actualizar campos
            existing.title = scheduled_alert.title
            existing.message = scheduled_alert.message
            existing.type = scheduled_alert.type.value
            existing.category = scheduled_alert.category.value
            existing.frequency = scheduled_alert.frequency.value
            existing.next_trigger_date = scheduled_alert.next_trigger_date
            existing.days_before_warning = scheduled_alert.days_before_warning
            existing.is_active = scheduled_alert.is_active
            existing.device_id = scheduled_alert.device_id
            existing.device_name = scheduled_alert.device_name
            existing.custom_days_interval = scheduled_alert.custom_days_interval
            existing.metadata_json = scheduled_alert.metadata
            existing.last_triggered_at = scheduled_alert.last_triggered_at
            existing.user_id = scheduled_alert.user_id.value if scheduled_alert.user_id else existing.user_id
        else:
            # Crear nuevo registro
            model = ScheduledAlertModel.from_domain(scheduled_alert)
            self.session.add(model)

        await self.session.flush()

    async def find_by_id(self, alert_id: ScheduledAlertId, user_id: UserId) -> Optional[ScheduledAlert]:
        """Busca una alerta programada por su ID, filtrado por usuario."""
        query = (
            select(ScheduledAlertModel)
            .where(ScheduledAlertModel.id == alert_id.value)
            .where(ScheduledAlertModel.user_id == user_id.value)
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        return model.to_domain() if model else None

    async def get_all(self, user_id: UserId) -> List[ScheduledAlert]:
        """Obtiene todas las alertas programadas del usuario."""
        result = await self.session.execute(
            select(ScheduledAlertModel)
            .where(ScheduledAlertModel.user_id == user_id.value)
            .order_by(ScheduledAlertModel.next_trigger_date)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_active(self, user_id: UserId) -> List[ScheduledAlert]:
        """Obtiene solo las alertas programadas activas del usuario."""
        result = await self.session.execute(
            select(ScheduledAlertModel)
            .where(ScheduledAlertModel.user_id == user_id.value)
            .where(ScheduledAlertModel.is_active.is_(True))
            .order_by(ScheduledAlertModel.next_trigger_date)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def delete(self, alert_id: ScheduledAlertId, user_id: UserId) -> None:
        """Elimina una alerta programada del usuario."""
        query = (
            select(ScheduledAlertModel)
            .where(ScheduledAlertModel.id == alert_id.value)
            .where(ScheduledAlertModel.user_id == user_id.value)
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if model:
            await self.session.delete(model)
            await self.session.flush()
