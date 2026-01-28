"""
Tests unitarios para FeedingSession aggregate.

Estos tests verifican la lógica de negocio del agregado:
- Creación de sesiones
- Inicio y detención de operaciones
- Pausa y reanudación
- Actualización de parámetros
- Validación de reglas de negocio
- Gestión de eventos
- Cierre de sesión
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from domain.aggregates.feeding_session import FeedingSession
from domain.dtos import MachineConfiguration
from domain.enums import FeedingEventType, OperationStatus, SessionStatus
from domain.strategies.manual import ManualFeedingStrategy
from domain.value_objects import CageId, LineId, Weight


@pytest.fixture
def line_id():
    """Fixture que proporciona un LineId."""
    return LineId.generate()


@pytest.fixture
def cage_id():
    """Fixture que proporciona un CageId."""
    return CageId.generate()


@pytest.fixture
def mock_machine():
    """Fixture que proporciona un mock del servicio de máquina."""
    machine = AsyncMock()
    machine.send_configuration = AsyncMock()
    machine.stop = AsyncMock()
    machine.pause = AsyncMock()
    machine.resume = AsyncMock()
    return machine


@pytest.fixture
def manual_strategy():
    """Fixture que proporciona una estrategia manual."""
    return ManualFeedingStrategy(
        target_slot=1, blower_speed=70.0, doser_speed=50.0, target_amount_kg=100.0
    )


class TestFeedingSession_Creation:
    """Tests para creación de sesiones."""

    def test_session_created_with_active_status(self, line_id):
        """Debe crear sesión con status ACTIVE."""
        session = FeedingSession(line_id=line_id)

        assert session.status == SessionStatus.ACTIVE
        assert session.line_id == line_id
        assert session.total_dispensed_kg == Weight.zero()
        assert session.current_operation is None

    def test_session_has_unique_id(self, line_id):
        """Debe generar ID único para cada sesión."""
        session1 = FeedingSession(line_id=line_id)
        session2 = FeedingSession(line_id=line_id)

        assert session1.id != session2.id

    def test_session_has_current_date(self, line_id):
        """Debe asignar fecha actual."""
        session = FeedingSession(line_id=line_id)

        assert session.date.date() == datetime.utcnow().date()

    def test_session_initializes_empty_dispensed_by_slot(self, line_id):
        """Debe inicializar dispensed_by_slot vacío."""
        session = FeedingSession(line_id=line_id)

        assert session.dispensed_by_slot == {}


class TestFeedingSession_StartOperation:
    """Tests para inicio de operaciones."""

    @pytest.mark.asyncio
    async def test_start_operation_creates_new_operation(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe crear una nueva operación."""
        session = FeedingSession(line_id=line_id)

        operation_id = await session.start_operation(
            cage_id=cage_id,
            target_slot=1,
            strategy=manual_strategy,
            machine=mock_machine,
        )

        assert session.current_operation is not None
        assert session.current_operation.id == operation_id
        assert session.current_operation.status == OperationStatus.RUNNING
        assert session.current_operation.cage_id == cage_id

    @pytest.mark.asyncio
    async def test_start_operation_sends_config_to_machine(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe enviar configuración al PLC."""
        session = FeedingSession(line_id=line_id)

        await session.start_operation(
            cage_id=cage_id,
            target_slot=1,
            strategy=manual_strategy,
            machine=mock_machine,
        )

        mock_machine.send_configuration.assert_called_once()
        args = mock_machine.send_configuration.call_args
        assert args[0][0] == line_id  # line_id
        assert isinstance(args[0][1], MachineConfiguration)  # config

    @pytest.mark.asyncio
    async def test_start_operation_initializes_slot_counter(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe inicializar contador de slot si no existe."""
        session = FeedingSession(line_id=line_id)

        await session.start_operation(
            cage_id=cage_id,
            target_slot=1,
            strategy=manual_strategy,
            machine=mock_machine,
        )

        assert 1 in session.dispensed_by_slot
        assert session.dispensed_by_slot[1] == Weight.zero()

    @pytest.mark.asyncio
    async def test_start_operation_rejects_if_operation_active(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe rechazar si ya hay operación activa."""
        session = FeedingSession(line_id=line_id)

        # Primera operación
        await session.start_operation(
            cage_id=cage_id,
            target_slot=1,
            strategy=manual_strategy,
            machine=mock_machine,
        )

        # Intentar segunda operación
        with pytest.raises(ValueError) as exc_info:
            await session.start_operation(
                cage_id=cage_id,
                target_slot=2,
                strategy=manual_strategy,
                machine=mock_machine,
            )

        assert "operación activa" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_start_operation_logs_event(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe registrar evento de sesión."""
        session = FeedingSession(line_id=line_id)

        await session.start_operation(
            cage_id=cage_id,
            target_slot=1,
            strategy=manual_strategy,
            machine=mock_machine,
        )

        events = session.pop_events()
        assert len(events) >= 1
        assert events[0].type == FeedingEventType.COMMAND


class TestFeedingSession_StopOperation:
    """Tests para detención de operaciones."""

    @pytest.mark.asyncio
    async def test_stop_operation_stops_current_operation(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe detener la operación actual."""
        session = FeedingSession(line_id=line_id)
        await session.start_operation(cage_id, 1, manual_strategy, mock_machine)

        await session.stop_current_operation(mock_machine)

        assert session.current_operation is None

    @pytest.mark.asyncio
    async def test_stop_operation_sends_stop_to_machine(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe enviar comando STOP al PLC."""
        session = FeedingSession(line_id=line_id)
        await session.start_operation(cage_id, 1, manual_strategy, mock_machine)

        await session.stop_current_operation(mock_machine)

        mock_machine.stop.assert_called_once_with(line_id)

    @pytest.mark.asyncio
    async def test_stop_operation_idempotent(self, line_id, mock_machine):
        """Debe ser idempotente si no hay operación."""
        session = FeedingSession(line_id=line_id)

        # No debe fallar
        await session.stop_current_operation(mock_machine)

    @pytest.mark.asyncio
    async def test_stop_operation_logs_event(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe registrar evento de sesión."""
        session = FeedingSession(line_id=line_id)
        await session.start_operation(cage_id, 1, manual_strategy, mock_machine)
        session.pop_events()  # Limpiar eventos anteriores

        await session.stop_current_operation(mock_machine)

        events = session.pop_events()
        assert len(events) >= 1


class TestFeedingSession_PauseResume:
    """Tests para pausa y reanudación."""

    @pytest.mark.asyncio
    async def test_pause_operation_pauses_current_operation(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe pausar la operación actual."""
        session = FeedingSession(line_id=line_id)
        await session.start_operation(cage_id, 1, manual_strategy, mock_machine)

        await session.pause_current_operation(mock_machine)

        assert session.current_operation.status == OperationStatus.PAUSED

    @pytest.mark.asyncio
    async def test_pause_operation_sends_pause_to_machine(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe enviar comando PAUSE al PLC."""
        session = FeedingSession(line_id=line_id)
        await session.start_operation(cage_id, 1, manual_strategy, mock_machine)

        await session.pause_current_operation(mock_machine)

        mock_machine.pause.assert_called_once_with(line_id)

    @pytest.mark.asyncio
    async def test_pause_operation_rejects_if_no_operation(self, line_id, mock_machine):
        """Debe fallar si no hay operación activa."""
        session = FeedingSession(line_id=line_id)

        with pytest.raises(ValueError):
            await session.pause_current_operation(mock_machine)

    @pytest.mark.asyncio
    async def test_resume_operation_resumes_paused_operation(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe reanudar operación pausada."""
        session = FeedingSession(line_id=line_id)
        await session.start_operation(cage_id, 1, manual_strategy, mock_machine)
        await session.pause_current_operation(mock_machine)

        await session.resume_current_operation(mock_machine)

        assert session.current_operation.status == OperationStatus.RUNNING

    @pytest.mark.asyncio
    async def test_resume_operation_sends_resume_to_machine(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe enviar comando RESUME al PLC."""
        session = FeedingSession(line_id=line_id)
        await session.start_operation(cage_id, 1, manual_strategy, mock_machine)
        await session.pause_current_operation(mock_machine)

        await session.resume_current_operation(mock_machine)

        mock_machine.resume.assert_called_once_with(line_id)


class TestFeedingSession_CloseSession:
    """Tests para cierre de sesión."""

    def test_close_session_sets_status_closed(self, line_id):
        """Debe cambiar status a CLOSED."""
        session = FeedingSession(line_id=line_id)

        session.close_session()

        assert session.status == SessionStatus.CLOSED

    @pytest.mark.asyncio
    async def test_close_session_rejects_if_operation_active(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe rechazar si hay operación activa."""
        session = FeedingSession(line_id=line_id)
        await session.start_operation(cage_id, 1, manual_strategy, mock_machine)

        with pytest.raises(ValueError) as exc_info:
            session.close_session()

        assert "operación activa" in str(exc_info.value).lower()


class TestFeedingSession_DailySummary:
    """Tests para generación de resumen diario."""

    def test_get_daily_summary_structure(self, line_id):
        """Debe retornar estructura correcta."""
        session = FeedingSession(line_id=line_id)

        summary = session.get_daily_summary()

        assert "session_id" in summary
        assert "date" in summary
        assert "status" in summary
        assert "total_kg" in summary
        assert "details_by_slot" in summary
        assert "current_operation" in summary

    @pytest.mark.asyncio
    async def test_get_daily_summary_with_operation(
        self, line_id, cage_id, manual_strategy, mock_machine
    ):
        """Debe incluir información de operación actual."""
        session = FeedingSession(line_id=line_id)
        await session.start_operation(cage_id, 1, manual_strategy, mock_machine)

        summary = session.get_daily_summary()

        assert summary["current_operation"] is not None
        assert "operation_id" in summary["current_operation"]
        assert "cage_id" in summary["current_operation"]
        assert "status" in summary["current_operation"]
