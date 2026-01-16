"""
Tests de integración para StartFeedingSessionUseCase.

Estos tests verifican que el caso de uso cumple su contrato:
- Crear sesiones nuevas cuando no existen
- Reutilizar sesiones activas del mismo día
- Cerrar sesiones antiguas (de días anteriores)
- Validar que la línea existe
- Validar que la jaula existe y tiene slot asignado
- Validar que no hay operación activa antes de iniciar
- Iniciar operaciones correctamente
- Enviar configuración al PLC
"""

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from application.use_cases.feeding.start_feeding_use_case import (
    StartFeedingSessionUseCase,
)
from application.dtos.feeding_dtos import StartFeedingRequest
from domain.aggregates.feeding_session import FeedingSession
from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.aggregates.cage import Cage
from domain.enums import FeedingMode, SessionStatus, OperationStatus
from domain.value_objects import (
    LineId,
    LineName,
    CageId,
    CageName,
    SiloId,
    SiloName,
    Weight,
)
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
def use_case(repositories, machine_service):
    """Fixture que proporciona una instancia del caso de uso."""
    return StartFeedingSessionUseCase(
        session_repository=repositories["session_repo"],
        operation_repository=repositories["operation_repo"],
        line_repository=repositories["line_repo"],
        cage_repository=repositories["cage_repo"],
        machine_service=machine_service,
    )


@pytest.fixture
async def setup_basic_infrastructure(repositories):
    """Fixture que configura línea y jaula básica para tests."""
    factory = ComponentFactory()

    # Crear línea de alimentación
    line_id = LineId.generate()
    line = factory.create_feeding_line(
        line_id=line_id,
        line_name=LineName("Línea Test 1"),
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

    # Crear jaula y asignarla a slot 1
    cage_id = CageId.generate()
    cage = Cage(name=CageName("Jaula Test 1"))
    cage._id = cage_id
    cage.assign_to_line(line_id, slot_number=1)
    await repositories["cage_repo"].save(cage)

    # Agregar slot assignment a la línea
    line.assign_cage_to_slot(slot_number=1, cage_id=cage_id)
    await repositories["line_repo"].save(line)

    return {"line_id": line_id, "cage_id": cage_id, "line": line, "cage": cage}


class TestStartFeeding_BasicFlow:
    """Tests para el flujo básico de inicio de alimentación."""

    @pytest.mark.asyncio
    async def test_start_feeding_creates_new_session(
        self, use_case, setup_basic_infrastructure
    ):
        """Debe crear una nueva sesión cuando no existe ninguna."""
        infra = await setup_basic_infrastructure

        request = StartFeedingRequest(
            line_id=infra["line_id"].value,
            cage_id=infra["cage_id"].value,
            mode=FeedingMode.MANUAL,
            target_amount_kg=100.0,
            blower_speed_percentage=70.0,
            dosing_rate_kg_min=50.0,
        )

        operation_id = await use_case.execute(request)

        # Verificar que se creó la sesión
        session = await use_case.session_repository.find_active_by_line_id(
            infra["line_id"]
        )
        assert session is not None
        assert session.status == SessionStatus.ACTIVE
        assert session.line_id == infra["line_id"]

        # Verificar que se creó la operación
        assert isinstance(operation_id, UUID)
        operation = await use_case.operation_repository.find_current_by_session(
            session.id
        )
        assert operation is not None
        assert operation.status == OperationStatus.RUNNING
        assert operation.cage_id == infra["cage_id"]
        assert operation.target_slot == 1
        assert operation.target_amount == Weight.from_kg(100.0)

    @pytest.mark.asyncio
    async def test_start_feeding_reuses_active_session(
        self, use_case, setup_basic_infrastructure, repositories
    ):
        """Debe reutilizar sesión activa existente del mismo día."""
        infra = await setup_basic_infrastructure

        # Crear sesión existente
        existing_session = FeedingSession(line_id=infra["line_id"])
        await repositories["session_repo"].save(existing_session)
        existing_session_id = existing_session.id

        request = StartFeedingRequest(
            line_id=infra["line_id"].value,
            cage_id=infra["cage_id"].value,
            mode=FeedingMode.MANUAL,
            target_amount_kg=100.0,
            blower_speed_percentage=70.0,
            dosing_rate_kg_min=50.0,
        )

        operation_id = await use_case.execute(request)

        # Verificar que reutilizó la misma sesión
        session = await repositories["session_repo"].find_active_by_line_id(
            infra["line_id"]
        )
        assert session.id == existing_session_id

        # Pero creó nueva operación
        operation = await repositories["operation_repo"].find_by_id(
            await use_case.operation_repository.find_current_by_session(session.id).id
        )
        assert operation is not None

    @pytest.mark.asyncio
    async def test_start_feeding_sends_config_to_plc(
        self, use_case, setup_basic_infrastructure, machine_service
    ):
        """Debe enviar configuración al PLC."""
        infra = await setup_basic_infrastructure

        request = StartFeedingRequest(
            line_id=infra["line_id"].value,
            cage_id=infra["cage_id"].value,
            mode=FeedingMode.MANUAL,
            target_amount_kg=100.0,
            blower_speed_percentage=70.0,
            dosing_rate_kg_min=50.0,
        )

        await use_case.execute(request)

        # Verificar que el PLC recibió la configuración
        plc_status = await machine_service.get_status(infra["line_id"])
        assert plc_status.is_running is True
        assert plc_status.current_mode == FeedingMode.MANUAL


class TestStartFeeding_Validation:
    """Tests para validaciones del caso de uso."""

    @pytest.mark.asyncio
    async def test_start_feeding_validates_line_exists(self, use_case):
        """Debe fallar si la línea no existe."""
        fake_line_id = LineId.generate()
        fake_cage_id = CageId.generate()

        request = StartFeedingRequest(
            line_id=fake_line_id.value,
            cage_id=fake_cage_id.value,
            mode=FeedingMode.MANUAL,
            target_amount_kg=100.0,
            blower_speed_percentage=70.0,
            dosing_rate_kg_min=50.0,
        )

        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(request)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_start_feeding_validates_cage_exists(
        self, use_case, setup_basic_infrastructure
    ):
        """Debe fallar si la jaula no existe."""
        infra = await setup_basic_infrastructure
        fake_cage_id = CageId.generate()

        request = StartFeedingRequest(
            line_id=infra["line_id"].value,
            cage_id=fake_cage_id.value,
            mode=FeedingMode.MANUAL,
            target_amount_kg=100.0,
            blower_speed_percentage=70.0,
            dosing_rate_kg_min=50.0,
        )

        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(request)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_start_feeding_validates_cage_has_slot(self, use_case, repositories):
        """Debe fallar si la jaula no tiene slot asignado."""
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

        # Crear jaula SIN asignar slot
        cage_id = CageId.generate()
        cage = Cage(name=CageName("Jaula Sin Slot"))
        cage._id = cage_id
        # NO asignamos slot
        await repositories["cage_repo"].save(cage)

        request = StartFeedingRequest(
            line_id=line_id.value,
            cage_id=cage_id.value,
            mode=FeedingMode.MANUAL,
            target_amount_kg=100.0,
            blower_speed_percentage=70.0,
            dosing_rate_kg_min=50.0,
        )

        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(request)

        assert "does not have a physical slot" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_feeding_rejects_if_operation_active(
        self, use_case, setup_basic_infrastructure, repositories
    ):
        """Debe fallar si ya hay una operación activa."""
        infra = await setup_basic_infrastructure

        # Crear sesión con operación activa
        session = FeedingSession(line_id=infra["line_id"])
        await repositories["session_repo"].save(session)

        # Simular operación activa en dominio
        from domain.entities.feeding_operation import FeedingOperation
        from domain.strategies.manual import ManualFeedingStrategy

        strategy = ManualFeedingStrategy(
            target_slot=1, blower_speed=70.0, doser_speed=50.0, target_amount_kg=100.0
        )

        # Cargar sesión y agregar operación manualmente
        loaded_session = await repositories["session_repo"].find_active_by_line_id(
            infra["line_id"]
        )
        operation = FeedingOperation(
            session_id=loaded_session.id,
            cage_id=infra["cage_id"],
            target_slot=1,
            target_amount=Weight.from_kg(100.0),
            applied_config={"test": "config"},
        )
        await repositories["operation_repo"].save(operation)
        loaded_session._current_operation = operation

        # Intentar iniciar otra operación
        request = StartFeedingRequest(
            line_id=infra["line_id"].value,
            cage_id=infra["cage_id"].value,
            mode=FeedingMode.MANUAL,
            target_amount_kg=100.0,
            blower_speed_percentage=70.0,
            dosing_rate_kg_min=50.0,
        )

        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(request)

        assert "operación activa" in str(exc_info.value).lower()


class TestStartFeeding_SessionManagement:
    """Tests para gestión de sesiones (day boundary)."""

    @pytest.mark.asyncio
    async def test_start_feeding_closes_old_session(
        self, use_case, setup_basic_infrastructure, repositories
    ):
        """Debe cerrar sesión de ayer y crear nueva."""
        infra = await setup_basic_infrastructure

        # Crear sesión de ayer
        old_session = FeedingSession(line_id=infra["line_id"])
        old_session._date = datetime.utcnow() - timedelta(days=1)
        await repositories["session_repo"].save(old_session)
        old_session_id = old_session.id

        request = StartFeedingRequest(
            line_id=infra["line_id"].value,
            cage_id=infra["cage_id"].value,
            mode=FeedingMode.MANUAL,
            target_amount_kg=100.0,
            blower_speed_percentage=70.0,
            dosing_rate_kg_min=50.0,
        )

        await use_case.execute(request)

        # Verificar que la sesión vieja fue cerrada
        old_session_after = await repositories["session_repo"].find_by_id(
            old_session_id
        )
        assert old_session_after.status == SessionStatus.CLOSED

        # Verificar que hay nueva sesión activa
        new_session = await repositories["session_repo"].find_active_by_line_id(
            infra["line_id"]
        )
        assert new_session is not None
        assert new_session.id != old_session_id
        assert new_session.date.date() == datetime.utcnow().date()

    @pytest.mark.asyncio
    async def test_start_feeding_accumulates_in_same_session(
        self, use_case, setup_basic_infrastructure, repositories, machine_service
    ):
        """Debe acumular múltiples operaciones en la misma sesión."""
        infra = await setup_basic_infrastructure

        # Primera operación
        request1 = StartFeedingRequest(
            line_id=infra["line_id"].value,
            cage_id=infra["cage_id"].value,
            mode=FeedingMode.MANUAL,
            target_amount_kg=50.0,
            blower_speed_percentage=70.0,
            dosing_rate_kg_min=50.0,
        )
        await use_case.execute(request1)
        session = await repositories["session_repo"].find_active_by_line_id(
            infra["line_id"]
        )
        session_id = session.id

        # Detener primera operación
        await machine_service.stop(infra["line_id"])
        session._current_operation.stop()
        await repositories["operation_repo"].save(session._current_operation)
        session._current_operation = None
        await repositories["session_repo"].save(session)

        # Segunda operación (misma sesión)
        request2 = StartFeedingRequest(
            line_id=infra["line_id"].value,
            cage_id=infra["cage_id"].value,
            mode=FeedingMode.MANUAL,
            target_amount_kg=75.0,
            blower_speed_percentage=70.0,
            dosing_rate_kg_min=50.0,
        )
        await use_case.execute(request2)

        # Verificar que sigue siendo la misma sesión
        session_after = await repositories["session_repo"].find_active_by_line_id(
            infra["line_id"]
        )
        assert session_after.id == session_id

        # Verificar que hay 2 operaciones en total
        all_operations = await repositories["operation_repo"].find_all_by_session(
            session_id
        )
        )
        await use_case.execute(request2)

        # Verificar que sigue siendo la misma sesión
        session_after = await repositories['session_repo'].find_active_by_line_id(infra['line_id'])
        assert session_after.id == session_id

        # Verificar que hay 2 operaciones en total
        all_operations = await repositories['operation_repo'].find_all_by_session(session_id)
        assert len(all_operations) == 2
