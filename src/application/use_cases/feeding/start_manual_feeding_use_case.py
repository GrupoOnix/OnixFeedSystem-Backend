import asyncio

from api.models.feeding_models import ManualFeedingRequest, ManualFeedingResponse
from application.services.feeding_orchestrator import FeedingOrchestrator
from domain.entities.cage_feeding import CageFeeding, CageFeedingMode
from domain.entities.feeding_event import FeedingEvent
from domain.entities.feeding_session import FeedingSession, FeedingType
from domain.enums import CageStatus
from domain.repositories import (
    ICageFeedingRepository,
    ICageRepository,
    IFeedingEventRepository,
    IFeedingLineRepository,
    IFeedingSessionRepository,
    ISiloRepository,
    ISlotAssignmentRepository,
    ISystemConfigRepository,
)
from domain.services.feeding_time_calculator import SELECTOR_POSITIONING_SECONDS, calculate_visit_duration
from domain.services.operating_schedule_service import OperatingScheduleService
from domain.value_objects import CageId, LineId
from domain.value_objects.identifiers import DoserId
from domain.value_objects.measurements import Weight


class StartManualFeedingUseCase:

    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        cage_feeding_repository: ICageFeedingRepository,
        event_repository: IFeedingEventRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        silo_repository: ISiloRepository,
        slot_assignment_repository: ISlotAssignmentRepository,
        orchestrator: FeedingOrchestrator,
        system_config_repository: ISystemConfigRepository,
    ):
        self.session_repo = session_repository
        self.cage_feeding_repo = cage_feeding_repository
        self.event_repo = event_repository
        self.line_repo = line_repository
        self.cage_repo = cage_repository
        self.silo_repo = silo_repository
        self.slot_assignment_repo = slot_assignment_repository
        self.orchestrator = orchestrator
        self.system_config_repo = system_config_repository

    async def execute(self, request: ManualFeedingRequest) -> ManualFeedingResponse:
        # Paso 1: VALIDACIÓN — retorna entidades ya cargadas para reutilizar
        line, cage, assignment = await self._validate_request(request)
        selected_doser = line.get_doser_by_id(DoserId.from_string(request.doser_id))
        assert selected_doser is not None

        estimated_seconds = calculate_visit_duration(
            quantity_kg=request.quantity_kg,
            rate_kg_per_min=request.rate_kg_per_min,
            transport_time_seconds=cage.config.transport_time_seconds,  # type: ignore[arg-type]
            blower=line.blower,
        )

        if not request.allow_overtime:
            config = await self.system_config_repo.get()
            OperatingScheduleService(config).assert_fits_in_window(estimated_seconds)

        # Paso 2: CREAR ENTIDADES
        session = FeedingSession(
            feeding_type=FeedingType.MANUAL,
            line_id=request.line_id,
            operator_id=request.operator_id,
            total_programmed_kg=request.quantity_kg,
            allow_overtime=request.allow_overtime,
        )
        session.start()

        cage_feeding = CageFeeding(
            feeding_session_id=session.id,
            cage_id=request.cage_id,
            doser_id=request.doser_id,
            silo_id=str(selected_doser.assigned_silo_id.value),
            execution_order=1,
            programmed_kg=request.quantity_kg,
            programmed_visits=1,
            rate_kg_per_min=request.rate_kg_per_min,
            mode=CageFeedingMode.NORMAL,
        )
        cage_feeding.start()

        session_started_event = FeedingEvent.session_started(
            feeding_session_id=session.id,
            operator_id=request.operator_id
        )

        # Paso 3: PERSISTIR
        await self.session_repo.save(session)
        await self.cage_feeding_repo.save(cage_feeding)
        await self.event_repo.save(session_started_event)

        # Paso 4: LANZAR ORQUESTADOR EN BACKGROUND
        asyncio.create_task(
            self.orchestrator.run(
                session=session,
                cage_feedings=[cage_feeding],
                line_id=LineId.from_string(request.line_id),
                slot_map={cage_feeding.cage_id: assignment.slot_number},
                silo_id=selected_doser.assigned_silo_id,
                blower_power_percentage=request.blower_power_percentage,
                transport_time_map={cage_feeding.cage_id: float(cage.config.transport_time_seconds)},  # type: ignore[arg-type]
                blow_before_seconds=float(line.blower.blow_before_feeding_time.value),
                blow_after_seconds=float(line.blower.blow_after_feeding_time.value),
                selector_positioning_seconds=SELECTOR_POSITIONING_SECONDS,
            )
        )

        return ManualFeedingResponse(
            session_id=session.id,
            cage_feeding_id=cage_feeding.id,
            estimated_duration_seconds=estimated_seconds,
            message="Alimentación manual iniciada exitosamente"
        )

    async def _validate_request(self, request: ManualFeedingRequest):
        #Línea existe?
        line = await self.line_repo.find_by_id(LineId.from_string(request.line_id))
        if not line:
            raise ValueError(f"Línea con ID {request.line_id} no encontrada")

        #Línea tiene sesión activa?
        active_session = await self.session_repo.find_active_by_line(request.line_id)
        if active_session:
            raise ValueError(
                f"La línea {request.line_id} ya tiene una sesión activa "
                f"(session_id: {active_session.id})"
            )

        #Jaula existe?
        cage = await self.cage_repo.find_by_id(CageId.from_string(request.cage_id))
        if not cage:
            raise ValueError(f"Jaula con ID {request.cage_id} no encontrada")

        #Jaula en mantenimiento?
        if cage.status == CageStatus.MAINTENANCE:
            raise ValueError(
                f"La jaula {cage.name.value} está en mantenimiento y no puede ser alimentada"
            )

        #Jaula pertenece a esta línea?
        assignment = await self.slot_assignment_repo.find_by_cage(CageId.from_string(request.cage_id))
        if not assignment:
            raise ValueError(f"La jaula {cage.name.value} no está asignada a ninguna línea")
        if str(assignment.line_id) != request.line_id:
            raise ValueError(
                f"La jaula {cage.name.value} está asignada a otra línea, no a {request.line_id}"
            )

        #Jaula tiene tiempo de transporte configurado?
        if cage.config.transport_time_seconds is None:
            raise ValueError(
                f"La jaula {cage.name.value} no tiene tiempo de transporte configurado. "
                "Debe configurarlo antes de iniciar una alimentación."
            )

        #Línea tiene dosers configurados?
        if not line.dosers:
            raise ValueError("La línea no tiene dosers configurados")

        #El doser solicitado existe en esta línea?
        selected_doser = line.get_doser_by_id(DoserId.from_string(request.doser_id))
        if not selected_doser:
            raise ValueError(
                f"El doser {request.doser_id} no existe en la línea {request.line_id}"
            )

        #Tasa solicitada no excede capacidad del doser seleccionado?
        if request.rate_kg_per_min > selected_doser.max_rate_kg_per_min:
            raise ValueError(
                f"La tasa solicitada ({request.rate_kg_per_min} kg/min) excede "
                f"la capacidad máxima del doser ({selected_doser.max_rate_kg_per_min} kg/min)"
            )

        #Silo del doser seleccionado tiene stock suficiente?
        silo = await self.silo_repo.find_by_id(selected_doser.assigned_silo_id)
        if not silo:
            raise ValueError(f"El doser {request.doser_id} no tiene un silo asignado")
        required = Weight.from_kg(request.quantity_kg)
        if silo.stock_level < required:
            raise ValueError(
                f"Stock insuficiente en el silo: disponible {silo.stock_level.as_kg:.2f} kg, "
                f"requerido {request.quantity_kg:.2f} kg"
            )

        return line, cage, assignment


