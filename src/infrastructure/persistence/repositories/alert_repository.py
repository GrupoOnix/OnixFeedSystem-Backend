"""Implementación del repositorio de alertas."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_, select, update, CursorResult
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
            existing.timestamp = alert.timestamp
            existing.read_at = alert.read_at
            existing.resolved_at = alert.resolved_at
            existing.resolved_by = alert.resolved_by
            existing.snoozed_until = alert.snoozed_until
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
        """Lista alertas con filtros opcionales. Excluye alertas silenciadas."""
        query = select(AlertModel)

        # Excluir alertas silenciadas (snoozed_until > now)
        now = datetime.utcnow()
        query = query.where(or_(AlertModel.snoozed_until.is_(None), AlertModel.snoozed_until <= now))

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

    async def count(
        self,
        status: Optional[List[AlertStatus]] = None,
        type: Optional[List[AlertType]] = None,
        category: Optional[List[AlertCategory]] = None,
        search: Optional[str] = None,
    ) -> int:
        """Cuenta alertas con filtros opcionales (sin paginación). Excluye silenciadas."""
        from sqlalchemy import func

        query = select(func.count(AlertModel.id))

        # Excluir alertas silenciadas (snoozed_until > now)
        now = datetime.utcnow()
        query = query.where(or_(AlertModel.snoozed_until.is_(None), AlertModel.snoozed_until <= now))

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

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_unread(self) -> int:
        """Cuenta la cantidad de alertas no leídas (excluyendo silenciadas)."""
        from sqlalchemy import func

        now = datetime.utcnow()
        query = (
            select(func.count(AlertModel.id))
            .where(AlertModel.status == AlertStatus.UNREAD.value)
            .where(or_(AlertModel.snoozed_until.is_(None), AlertModel.snoozed_until <= now))
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
        result: CursorResult = await self.session.execute(stmt)  # type: ignore[assignment]
        await self.session.flush()
        return result.rowcount or 0

    async def find_active_by_silo(self, silo_id: str) -> Optional[Alert]:
        """
        Busca una alerta activa (UNREAD o READ) para un silo específico.
        Excluye alertas silenciadas.

        Busca en los metadatos de las alertas de categoría INVENTORY.
        """
        now = datetime.utcnow()
        query = (
            select(AlertModel)
            .where(AlertModel.category == AlertCategory.INVENTORY.value)
            .where(AlertModel.status.in_([AlertStatus.UNREAD.value, AlertStatus.READ.value]))
            .where(or_(AlertModel.snoozed_until.is_(None), AlertModel.snoozed_until <= now))
            .order_by(AlertModel.timestamp.desc())
        )

        result = await self.session.execute(query)
        alert_models = result.scalars().all()

        # Filtrar por silo_id en los metadatos
        for model in alert_models:
            if model.metadata_json and model.metadata_json.get("silo_id") == silo_id:
                return model.to_domain()

        return None

    async def find_any_by_silo(self, silo_id: str) -> Optional[Alert]:
        """
        Busca cualquier alerta para un silo (incluyendo silenciadas).
        Busca en los metadatos de las alertas de categoría INVENTORY.
        """
        query = (
            select(AlertModel)
            .where(AlertModel.category == AlertCategory.INVENTORY.value)
            .where(AlertModel.status.in_([AlertStatus.UNREAD.value, AlertStatus.READ.value]))
            .order_by(AlertModel.timestamp.desc())
        )

        result = await self.session.execute(query)
        alert_models = result.scalars().all()

        # Filtrar por silo_id en los metadatos
        for model in alert_models:
            if model.metadata_json and model.metadata_json.get("silo_id") == silo_id:
                return model.to_domain()

        return None

    async def list_snoozed(self, limit: int = 50, offset: int = 0) -> tuple[List[Alert], int]:
        """Lista alertas actualmente silenciadas."""
        from sqlalchemy import func

        now = datetime.utcnow()

        # Contar total de alertas silenciadas
        count_query = select(func.count(AlertModel.id)).where(
            AlertModel.snoozed_until.isnot(None), AlertModel.snoozed_until > now
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Obtener alertas silenciadas con paginación
        query = (
            select(AlertModel)
            .where(AlertModel.snoozed_until.isnot(None))
            .where(AlertModel.snoozed_until > now)
            .order_by(AlertModel.snoozed_until.asc())  # Las que expiran primero
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        alert_models = result.scalars().all()
        alerts = [model.to_domain() for model in alert_models]

        return alerts, total

    async def count_snoozed(self) -> int:
        """Cuenta la cantidad de alertas actualmente silenciadas."""
        from sqlalchemy import func

        now = datetime.utcnow()
        query = select(func.count(AlertModel.id)).where(
            AlertModel.snoozed_until.isnot(None), AlertModel.snoozed_until > now
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_by_type(
        self,
        type: AlertType,
        exclude_resolved: bool = True,
        exclude_snoozed: bool = True,
    ) -> int:
        """Cuenta alertas por tipo."""
        from sqlalchemy import func

        now = datetime.utcnow()
        query = select(func.count(AlertModel.id)).where(AlertModel.type == type.value)

        # Excluir alertas resueltas si se solicita
        if exclude_resolved:
            query = query.where(AlertModel.status != AlertStatus.RESOLVED.value)

        # Excluir alertas silenciadas si se solicita
        if exclude_snoozed:
            query = query.where(or_(AlertModel.snoozed_until.is_(None), AlertModel.snoozed_until <= now))

        result = await self.session.execute(query)
        return result.scalar() or 0
