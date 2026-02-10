"""
Repositorio para operaciones de alimentación.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.feeding_operation import FeedingOperation, OperationEvent
from domain.enums import OperationStatus, OperationEventType
from domain.value_objects import OperationId, CageId, Weight, SessionId
from domain.repositories import IFeedingOperationRepository
from infrastructure.persistence.models.feeding_operation_model import FeedingOperationModel
from infrastructure.persistence.models.operation_event_model import OperationEventModel


class FeedingOperationRepository(IFeedingOperationRepository):
    """Implementación del repositorio de operaciones de alimentación."""

    def __init__(self, session: AsyncSession):
        self.db = session

    async def save(self, operation: FeedingOperation) -> None:
        """Guarda/actualiza una operación individual."""

        # Intentar recuperar modelo existente
        op_model = await self.db.get(FeedingOperationModel, operation.id.value)

        if op_model:
            # UPDATE
            op_model.status = operation.status.value
            op_model.dispensed_kg = operation.dispensed.as_kg
            op_model.ended_at = operation.ended_at
            op_model.applied_config = operation.applied_config
        else:
            # INSERT (nueva operación)
            op_model = FeedingOperationModel(
                id=operation.id.value,
                session_id=operation.session_id.value,  # Necesita session_id
                cage_id=operation.cage_id.value,
                target_slot=operation.target_slot,
                target_amount_kg=operation.target_amount.as_kg,
                dispensed_kg=operation.dispensed.as_kg,
                status=operation.status.value,
                started_at=operation.started_at,
                ended_at=operation.ended_at,
                applied_config=operation.applied_config,
            )
            self.db.add(op_model)

        # Guardar solo eventos NUEVOS
        for event in operation.pop_new_events():
            event_model = OperationEventModel(
                id=uuid4(),
                operation_id=operation.id.value,
                timestamp=event.timestamp,
                type=event.type.value,
                description=event.description,
                details=event.details,
            )
            self.db.add(event_model)

        await self.db.flush()

    async def find_by_id(self, operation_id: OperationId) -> Optional[FeedingOperation]:
        """Busca una operación por su ID."""
        result = await self.db.execute(
            select(FeedingOperationModel).where(FeedingOperationModel.id == operation_id.value)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_current_by_session(self, session_id: SessionId) -> Optional[FeedingOperation]:
        """Encuentra la operación activa (RUNNING o PAUSED) de una sesión."""
        query = (
            select(FeedingOperationModel)
            .where(
                FeedingOperationModel.session_id == session_id.value,
                FeedingOperationModel.status.in_([OperationStatus.RUNNING.value, OperationStatus.PAUSED.value]),
            )
            .order_by(desc(FeedingOperationModel.started_at))
        )

        result = await self.db.execute(query)
        model = result.scalar_one_or_none()

        return self._to_domain(model) if model else None

    async def find_all_by_session(self, session_id: SessionId) -> List[FeedingOperation]:
        """Obtiene todas las operaciones de una sesión (para reportes)."""
        query = (
            select(FeedingOperationModel)
            .where(FeedingOperationModel.session_id == session_id.value)
            .order_by(FeedingOperationModel.started_at)
        )

        result = await self.db.execute(query)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: FeedingOperationModel) -> FeedingOperation:
        """Reconstruye la operación desde el modelo."""
        operation = FeedingOperation.__new__(FeedingOperation)
        operation._id = OperationId(model.id)
        operation._session_id = SessionId(model.session_id)  # Necesario para save
        operation._cage_id = CageId(model.cage_id)
        operation._target_slot = model.target_slot
        operation._target_amount = Weight.from_kg(model.target_amount_kg)
        operation._dispensed = Weight.from_kg(model.dispensed_kg)
        operation._status = OperationStatus(model.status)
        operation._started_at = model.started_at
        operation._ended_at = model.ended_at
        operation._applied_config = model.applied_config

        # Reconstruir eventos (todos)
        operation._events = [
            OperationEvent(
                timestamp=ev.timestamp, type=OperationEventType(ev.type), description=ev.description, details=ev.details
            )
            for ev in model.events
        ]
        operation._new_events = []  # No hay eventos nuevos al cargar

        return operation

    async def get_today_dispensed_by_cage(self, cage_id: CageId) -> float:
        """
        Calcula el total de alimento dispensado a una jaula en el día actual.

        Args:
            cage_id: ID de la jaula

        Returns:
            Total de kg dispensados hoy (desde las 00:00 UTC)
        """
        # Inicio del día actual (naive datetime para compatibilidad con DB)
        today_start = datetime.combine(date.today(), datetime.min.time())

        query = select(func.coalesce(func.sum(FeedingOperationModel.dispensed_kg), 0)).where(
            FeedingOperationModel.cage_id == cage_id.value,
            FeedingOperationModel.started_at >= today_start,
        )

        result = await self.db.execute(query)
        total = result.scalar_one()

        return float(total)

    async def get_today_dispensed_by_cages(self, cage_ids: List[CageId]) -> dict[str, float]:
        """
        Calcula el total de alimento dispensado para múltiples jaulas en el día actual.

        Args:
            cage_ids: Lista de IDs de jaulas

        Returns:
            Diccionario con cage_id (string) como clave y kg dispensados como valor
        """
        if not cage_ids:
            return {}

        # Inicio del día actual (naive datetime para compatibilidad con DB)
        today_start = datetime.combine(date.today(), datetime.min.time())

        # Convertir CageIds a UUIDs
        cage_uuid_list: List[UUID] = [cid.value for cid in cage_ids]

        query = (
            select(
                FeedingOperationModel.cage_id,
                func.coalesce(func.sum(FeedingOperationModel.dispensed_kg), 0).label("total_dispensed"),
            )
            .where(
                FeedingOperationModel.cage_id.in_(cage_uuid_list),
                FeedingOperationModel.started_at >= today_start,
            )
            .group_by(FeedingOperationModel.cage_id)
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Construir diccionario con todos los cage_ids, defaulting a 0
        dispensed_map: dict[str, float] = {str(cid.value): 0.0 for cid in cage_ids}
        for row in rows:
            dispensed_map[str(row.cage_id)] = float(row.total_dispensed)

        return dispensed_map
