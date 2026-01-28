"""
Tests de integración para StopFeedingSessionUseCase.

Estos tests verifican que el caso de uso cumple su contrato:
- Detener la operación actual correctamente
- Enviar comando STOP al PLC
- Actualizar estado de la operación a STOPPED
- Limpiar current_operation de la sesión
- Ser idempotente (no fallar si no hay operación activa)
"""


import pytest
from application.use_cases.feeding.stop_feeding_use_case import (
    StopFeedingSessionUseCase,
)
from application.use_cases.feeding.start_feeding_use_case import (
    StartFeedingSessionUseCase,
)
from application.dtos.feeding_dtos import StartFeedingRequest
from domain.aggregates.feeding_session import FeedingSession
from domain.aggregates.cage import Cage
from domain.enums import FeedingMode, OperationStatus
from domain.value_objects import LineId, LineName, CageId, CageName, SiloId, Weight
from domain.factories import ComponentFactory
from infrastructure.persistence.mock_repositories import (
    MockFeedingLineRepository,
    MockCageRepository,
    MockFeedingSessionRepository,
    MockFeedingOperationRepository,
)
from infrastructure.services.plc_simulator import PLCSimulator


@pytest.fixture
def repositories():
    """Fixture que proporciona repositorios mock limpios."""
    return {
        "session_repo": MockFeedingSessionRepository(),
        "operation_repo": MockFeedingOperationRepository(),
        "line_repo": MockFeedingLineRepository(),
        "cage_repo": MockCageRepository(),
    }


@pytest.fixture
def machine_service():
    """Fixture que proporciona el simulador PLC."""
    return PLCSimulator(enable_detailed_logging=False)


@pytest.fixture
def stop_use_case(repositories, machine_service):
    """Fixture que proporciona instancia del caso de uso Stop."""
    return StopFeedingSessionUseCase(
        session_repository=repositories["session_repo"],
        operation_repository=repositories["operation_repo"],
        machine_service=machine_service,
    )


@pytest.fixture
def start_use_case(repositories, machine_service):
    """Fixture que proporciona instancia del caso de uso Start (para setup)."""
    return StartFeedingSessionUseCase(
        session_repository=repositories["session_repo"],
        operation_repository=repositories["operation_repo"],
        line_repository=repositories["line_repo"],
        cage_repository=repositories["cage_repo"],
        machine_service=machine_service,
    )


@pytest.fixture
async def setup_active_operation(repositories, start_use_case):
    """Fixture que configura una operación activa lista para detener."""
    factory = ComponentFactory()

    # Crear línea
    line_id = LineId.generate()
    line = factory.create_feeding_line(
        line_id=line_id,
        line_name=LineName("Línea Test"),
        blower_name="Soplador 1",
        blower_non_feeding_power=50.0,
        blower_blow_before=5,
        blower_blow_after=3,
        selector_name="Selector 1",
        selector_capacity=4,
        selector_fast_speed=80.0,
        selector_slow_speed=20.0,
        doser_configs=[
            {
                "name": "Dosificador 1",
                "assigned_silo_id": SiloId.generate(),
                "doser_type": "volumetric",
                "min_rate": 10.0,
                "max_rate": 100.0,
                "current_rate": 50.0,
            }
        ],
        sensor_configs=[],
    )
    await repositories["line_repo"].save(line)

    # Crear jaula con slot
    cage_id = CageId.generate()
    cage = Cage(name=CageName("Jaula Test"))
    cage._id = cage_id
    cage.assign_to_line(line_id, slot_number=1)
    await repositories["cage_repo"].save(cage)
    line.assign_cage_to_slot(slot_number=1, cage_id=cage_id)
    await repositories["line_repo"].save(line)

    # Iniciar operación
    request = StartFeedingRequest(
        line_id=line_id.value,
        cage_id=cage_id.value,
        mode=FeedingMode.MANUAL,
        target_amount_kg=100.0,
        blower_speed_percentage=70.0,
        dosing_rate_kg_min=50.0,
    )
    operation_id = await start_use_case.execute(request)

    return {"line_id": line_id, "cage_id": cage_id, "operation_id": operation_id}


class TestStopFeeding_BasicFlow:
    """Tests para el flujo básico de detención."""

    @pytest.mark.asyncio
    async def test_stop_feeding_stops_operation(
        self, stop_use_case, setup_active_operation, repositories
    ):
        """Debe detener la operación activa correctamente."""
        infra = await setup_active_operation

        await stop_use_case.execute(infra["line_id"].value)

        # Verificar que la operación fue detenida
        session = await repositories["session_repo"].find_active_by_line_id(
            infra["line_id"]
        )
        assert session.current_operation is None  # Operación liberada

        # Verificar estado de la operación en repositorio
        from domain.value_objects import OperationId

        operation = await repositories["operation_repo"].find_by_id(
            OperationId(infra["operation_id"])
        )
        assert operation.status == OperationStatus.STOPPED

    @pytest.mark.asyncio
    async def test_stop_feeding_sends_stop_to_plc(
        self, stop_use_case, setup_active_operation, machine_service
    ):
        """Debe enviar comando STOP al PLC."""
        infra = await setup_active_operation

        # Verificar que PLC está corriendo antes
        status_before = await machine_service.get_status(infra["line_id"])
        assert status_before.is_running is True

        await stop_use_case.execute(infra["line_id"].value)

        # Verificar que PLC fue detenido
        status_after = await machine_service.get_status(infra["line_id"])
        assert status_after.is_running is False

    @pytest.mark.asyncio
    async def test_stop_feeding_preserves_session(
        self, stop_use_case, setup_active_operation, repositories
    ):
        """Debe mantener la sesión activa después de detener la operación."""
        infra = await setup_active_operation

        session_before = await repositories["session_repo"].find_active_by_line_id(
            infra["line_id"]
        )
        session_id = session_before.id

        await stop_use_case.execute(infra["line_id"].value)

        # Verificar que la sesión sigue activa
        session_after = await repositories["session_repo"].find_active_by_line_id(
            infra["line_id"]
        )
        assert session_after is not None
        assert session_after.id == session_id

    @pytest.mark.asyncio
    async def test_stop_feeding_records_dispensed_amount(
        self, stop_use_case, setup_active_operation, repositories
    ):
        """Debe registrar la cantidad dispensada antes de detener."""
        infra = await setup_active_operation

        # Simular dispensado
        operation = await repositories["operation_repo"].find_by_id(
            await repositories["operation_repo"]
            .find_current_by_session(
                (
                    await repositories["session_repo"].find_active_by_line_id(
                        infra["line_id"]
                    )
                ).id
            )
            .id
        )
        operation.add_dispensed_amount(Weight.from_kg(50.0))
        await repositories["operation_repo"].save(operation)

        await stop_use_case.execute(infra["line_id"].value)

        # Verificar que se registró el dispensado
        from domain.value_objects import OperationId

        stopped_operation = await repositories["operation_repo"].find_by_id(
            OperationId(infra["operation_id"])
        )
        assert stopped_operation.dispensed == Weight.from_kg(50.0)


class TestStopFeeding_Idempotence:
    """Tests para idempotencia del caso de uso."""

    @pytest.mark.asyncio
    async def test_stop_feeding_idempotent_no_session(self, stop_use_case):
        """Debe ser idempotente cuando no hay sesión activa."""
        fake_line_id = LineId.generate()

        # No debe lanzar excepción
        await stop_use_case.execute(fake_line_id.value)

    @pytest.mark.asyncio
    async def test_stop_feeding_idempotent_no_operation(
        self, stop_use_case, repositories
    ):
        """Debe ser idempotente cuando hay sesión pero no operación."""
        line_id = LineId.generate()

        # Crear sesión sin operación
        session = FeedingSession(line_id=line_id)
        await repositories["session_repo"].save(session)

        # No debe lanzar excepción
        await stop_use_case.execute(line_id.value)

    @pytest.mark.asyncio
    async def test_stop_feeding_idempotent_already_stopped(
        self, stop_use_case, setup_active_operation
    ):
        """Debe ser idempotente al llamar stop múltiples veces."""
        infra = await setup_active_operation

        # Primera detención
        await stop_use_case.execute(infra["line_id"].value)

        # Segunda detención (no debe fallar)
        await stop_use_case.execute(infra["line_id"].value)


class TestStopFeeding_EventLogging:
    """Tests para verificación de logging de eventos."""

    @pytest.mark.asyncio
    async def test_stop_feeding_logs_operation_event(
        self, stop_use_case, setup_active_operation, repositories
    ):
        """Debe registrar evento de STOPPED en la operación."""
        infra = await setup_active_operation

        await stop_use_case.execute(infra["line_id"].value)

        # Verificar que se registraron eventos
        from domain.value_objects import OperationId

        operation = await repositories["operation_repo"].find_by_id(
            OperationId(infra["operation_id"])
        )

        # Debe tener al menos 2 eventos: STARTED y STOPPED
        assert len(operation.events) >= 2

        # Último evento debe ser STOPPED
        from domain.enums import OperationEventType


        # Último evento debe ser STOPPED
        assert operation.events[-1].type == OperationEventType.STOPPED
