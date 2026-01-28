from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from domain.aggregates.feeding_session import FeedingSession
from domain.repositories import IFeedingSessionRepository
from domain.value_objects import SessionId, LineId, Weight
from domain.enums import SessionStatus
from infrastructure.persistence.models.feeding_session_model import FeedingSessionModel
from infrastructure.persistence.models.feeding_event_model import FeedingEventModel

class FeedingSessionRepository(IFeedingSessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, feeding_session: FeedingSession) -> None:
        """Guarda solo la sesión (acumuladores y estado)."""

        # 1. Intentar recuperar el modelo existente (Para decidir si es UPDATE o INSERT)
        session_model = await self.session.get(FeedingSessionModel, feeding_session.id.value)

        # Preparar datos JSON
        details_json = {str(k): v.as_kg for k, v in feeding_session.dispensed_by_slot.items()}

        if session_model:
            # --- ACTUALIZACIÓN ---
            # Solo actualizamos los campos mutables
            session_model.status = feeding_session.status.value
            session_model.total_dispensed_kg = feeding_session.total_dispensed_kg.as_kg
            session_model.dispensed_by_slot = details_json
            # applied_strategy_config ELIMINADO (ahora está en FeedingOperation)
        else:
            # --- CREACIÓN ---
            # Es una sesión nueva, creamos el modelo desde cero
            session_model = FeedingSessionModel(
                id=feeding_session.id.value,
                line_id=feeding_session.line_id.value,
                date=feeding_session.date,
                status=feeding_session.status.value,
                total_dispensed_kg=feeding_session.total_dispensed_kg.as_kg,
                dispensed_by_slot=details_json
            )
            self.session.add(session_model)

        # 2. Guardar Eventos de Sesión (solo eventos de sesión, no de operación)
        new_events = feeding_session.pop_events()

        for event in new_events:
            event_model = FeedingEventModel(
                session_id=feeding_session.id.value,
                timestamp=event.timestamp,
                event_type=event.type.value,  # Usar .value para Enums
                description=event.description,
                details=event.details
            )
            self.session.add(event_model)

        # 3. Flush en lugar de Commit
        await self.session.flush()

    async def find_by_id(self, session_id: SessionId) -> Optional[FeedingSession]:
        query = select(FeedingSessionModel).where(FeedingSessionModel.id == session_id.value)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return self._to_domain(model)

    async def find_active_by_line_id(self, line_id: LineId) -> Optional[FeedingSession]:
        """Busca la sesión activa de una línea."""
        query = select(FeedingSessionModel).where(
            FeedingSessionModel.line_id == line_id.value,
            FeedingSessionModel.status == SessionStatus.ACTIVE.value
        ).order_by(desc(FeedingSessionModel.date))

        result = await self.session.execute(query)
        model = result.scalars().first()

        if not model:
            return None
        return self._to_domain(model)

    def _to_domain(self, model: FeedingSessionModel) -> FeedingSession:
        """Reconstruye el aggregate desde el modelo (sin operaciones)."""
        session = FeedingSession(LineId(model.line_id))

        # Restaurar identidad y estado (bypass de __init__)
        session._id = SessionId(model.id)
        session._date = model.date
        session._status = SessionStatus(model.status)
        session._total_dispensed_kg = Weight.from_kg(model.total_dispensed_kg)

        # Restaurar distribución por slot (JSON -> Dict[int, Weight])
        if model.dispensed_by_slot:
            session._dispensed_by_slot = {
                int(k): Weight.from_kg(v)
                for k, v in model.dispensed_by_slot.items()
            }
        else:
            session._dispensed_by_slot = {}

        # current_operation se carga por separado desde FeedingOperationRepository
        session._current_operation = None
        session._session_events = []

        return session
