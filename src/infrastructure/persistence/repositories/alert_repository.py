"""Implementación del repositorio de alertas."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.alert import Alert
from domain.enums import AlertCategory, AlertStatus, AlertType
from domain.repositories import IAlertRepository
from domain.value_objects import AlertId
from infrastructure.persistence.models.alert_model import AlertModel


class AlertRepository(IAlertRepository):
    """Implementación del repositorio de alertas."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, alert: Alert) -> None:
        """Guarda o actualiza una alerta."""
        existing = await self.session.get(AlertModel, alert.id.value)

        if existing:
            # Actualizar campos
            existing.type = alert.type.value
            existing.status = alert.status.value
            existing.category = alert.category.value
            existing.title = alert.title
            existing.message = alert.message
            existing.source = alert.source
            existing.read_at = alert.read_at
            existing.resolved_at = alert.resolved_at
            existing.resolved_by = alert.resolved_by
            existing.metadata_json = alert.metadata
        else:
            # Crear nuevo registro
            alert_model = AlertModel.from_domain(alert)
            self.session.add(alert_model)

        await self.session.flush()

    async def find_by_id(self, alert_id: AlertId) -> Optional[Alert]:
        """Busca una alerta por su ID."""
        alert_model = await self.session.get(AlertModel, alert_id.value)
        return alert_model.to_domain() if alert_model else None

    async def list(
        self,
        status: Optional[List[AlertStatus]] = None,
        type: Optional[List[AlertType]] = None,
        category: Optional[List[AlertCategory]] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Alert]:
        """Lista alertas con filtros opcionales."""
        query = select(AlertModel)

        # Aplicar filtros
        if status:
            status_values = [s.value for s in status]
            query = query.where(AlertModel.status.in_(status_values))

        if type:
            type_values = [t.value for t in type]
            query = query.where(AlertModel.type.in_(type_values))

        if category:
            category_values = [c.value for c in category]
            query = query.where(AlertModel.category.in_(category_values))

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    AlertModel.title.ilike(search_pattern),
                    AlertModel.message.ilike(search_pattern),
                    AlertModel.source.ilike(search_pattern),
                )
            )

        # Ordenar por timestamp descendente (más recientes primero)
        query = query.order_by(AlertModel.timestamp.desc())

        # Paginación
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        alert_models = result.scalars().all()
        return [model.to_domain() for model in alert_models]

    async def count_unread(self) -> int:
        """Cuenta la cantidad de alertas no leídas."""
        from sqlalchemy import func

        query = select(func.count(AlertModel.id)).where(
            AlertModel.status == AlertStatus.UNREAD.value
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def mark_all_as_read(self) -> int:
        """Marca todas las alertas UNREAD como READ."""
        now = datetime.utcnow()
        stmt = (
            update(AlertModel)
            .where(AlertModel.status == AlertStatus.UNREAD.value)
            .values(status=AlertStatus.READ.value, read_at=now)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount
