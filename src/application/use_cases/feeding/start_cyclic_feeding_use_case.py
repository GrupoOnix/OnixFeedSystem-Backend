import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from api.models.feeding_models import CageConfigInput, CyclicFeedingRequest, CyclicFeedingResponse
from application.services.feeding_orchestrator import FeedingOrchestrator
from domain.entities.cage_feeding import CageFeeding, CageFeedingMode
from domain.entities.feeding_event import FeedingEvent
from domain.entities.feeding_session import FeedingSession, FeedingType
from domain.enums import CageStatus
from domain.repositories import (
    ICageFeedingRepository,
    ICageGroupRepository,
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
from domain.value_objects.identifiers import CageGroupId, DoserId
from domain.value_objects.measurements import Weight


class StartCyclicFeedingUseCase:

    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        cage_feeding_repository: ICageFeedingRepository,
        event_repository: IFeedingEventRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        cage_group_repository: ICageGroupRepository,
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
        self.cage_group_repo = cage_group_repository
        self.silo_repo = silo_repository
        self.slot_assignment_repo = slot_assignment_repository
        self.orchestrator = orchestrator
        self.system_config_repo = system_config_repository

    async def execute(self, request: CyclicFeedingRequest) -> CyclicFeedingResponse:
        # Paso 1: Validar y cargar todas las entidades necesarias
        line, group, doser, cage_data = await self._validate_request(request)
        # cage_data: List[Tuple[CageConfigInput, cage, slot_assignment]]

        selected_doser = doser
        silo_id = selected_doser.assigned_silo_id

        # Paso 2: Calcular stock requerido (solo jaulas NORMAL)
        total_programmed_kg = sum(
            cfg.quantity_kg
            for cfg, _cage, _assignment in cage_data
            if cfg.mode == "NORMAL"
        )

        # Validar stock del silo
        silo = await self.silo_repo.find_by_id(silo_id)
        if not silo:
            raise ValueError(f"El doser {request.doser_id} no tiene un silo asignado")
        required = Weight.from_kg(total_programmed_kg)
        if silo.stock_level < required:
            raise ValueError(
                f"Stock insuficiente en el silo: disponible {silo.stock_level.as_kg:.2f} kg, "
                f"requerido {total_programmed_kg:.2f} kg"
            )

        # Paso 3: Ordenar por slot_number (orden físico de la línea)
        cage_data.sort(key=lambda item: item[2].slot_number)

        # Paso 4: Calcular duración estimada total
        blow_before = float(line.blower.blow_before_feeding_time.value)
        blow_after = float(line.blower.blow_after_feeding_time.value)

        estimated_total_seconds = 0.0
        for cfg, cage, _assignment in cage_data:
            if cfg.mode == "FASTING":
                continue
            transport_time = float(cage.config.transport_time_seconds)
            # Para PAUSE se calcula la duración simulada completa con sus kg/tasa
            kg_per_visit = round(cfg.quantity_kg / request.visits, 3)
            visit_seconds = calculate_visit_duration(
                quantity_kg=kg_per_visit,
                rate_kg_per_min=cfg.rate_kg_per_min,
                transport_time_seconds=transport_time,
                blower=line.blower,
            )
            estimated_total_seconds += visit_seconds * request.visits

        # Validar horario operativo
        if not request.allow_overtime:
            config = await self.system_config_repo.get()
            OperatingScheduleService(config).assert_fits_in_window(estimated_total_seconds)

        # Paso 5: Crear entidades de dominio
        session = FeedingSession(
            feeding_type=FeedingType.CYCLIC,
            line_id=request.line_id,
            operator_id=request.operator_id,
            total_programmed_kg=total_programmed_kg,
            allow_overtime=request.allow_overtime,
        )
        session.start()

        cage_feedings: List[CageFeeding] = []
        slot_map: Dict[str, int] = {}
        transport_time_map: Dict[str, float] = {}

        for execution_order, (cfg, cage, assignment) in enumerate(cage_data, start=1):
            mode = CageFeedingMode(cfg.mode)

            # FASTING: programmed_visits=0 → el orquestador la saltará
            programmed_visits = 0 if mode == CageFeedingMode.FASTING else request.visits

            # Calcular kg por visita (quantity_kg del request es el total para la jaula)
            kg_per_visit = round(cfg.quantity_kg / request.visits, 3) if programmed_visits > 0 else 0.0

            cage_feeding = CageFeeding(
                feeding_session_id=session.id,
                cage_id=str(cage.id.value),
                doser_id=request.doser_id,
                silo_id=str(silo_id.value),
                execution_order=execution_order,
                programmed_kg=kg_per_visit,
                programmed_visits=programmed_visits,
                rate_kg_per_min=cfg.rate_kg_per_min,
                mode=mode,
            )
            cage_feedings.append(cage_feeding)

            if mode != CageFeedingMode.FASTING:
                slot_map[str(cage.id.value)] = assignment.slot_number
                transport_time_map[str(cage.id.value)] = float(cage.config.transport_time_seconds)

        session_started_event = FeedingEvent.session_started(
            feeding_session_id=session.id,
            operator_id=request.operator_id,
        )

        # Paso 6: Persistir
        await self.session_repo.save(session)
        for cf in cage_feedings:
            await self.cage_feeding_repo.save(cf)
        await self.event_repo.save(session_started_event)

        # Paso 7: Lanzar orquestador en background
        asyncio.create_task(
            self.orchestrator.run(
                session=session,
                cage_feedings=cage_feedings,
                line_id=LineId.from_string(request.line_id),
                slot_map=slot_map,
                silo_id=silo_id,
                blower_power_percentage=request.blower_power_percentage,
                transport_time_map=transport_time_map,
                blow_before_seconds=blow_before,
                blow_after_seconds=blow_after,
                selector_positioning_seconds=SELECTOR_POSITIONING_SECONDS,
            )
        )

        return CyclicFeedingResponse(
            session_id=session.id,
            cage_feeding_ids=[cf.id for cf in cage_feedings],
            total_programmed_kg=total_programmed_kg,
            estimated_total_seconds=estimated_total_seconds,
            estimated_total_minutes=round(estimated_total_seconds / 60, 2),
            message="Alimentación cíclica iniciada exitosamente",
        )

    async def _validate_request(self, request: CyclicFeedingRequest):
        """
        Valida todos los prerequisitos y retorna las entidades cargadas.
        Retorna: (line, group, doser, cage_data)
        donde cage_data es List[Tuple[CageConfigInput, Cage, SlotAssignment]]
        """
        # Línea existe?
        line = await self.line_repo.find_by_id(LineId.from_string(request.line_id))
        if not line:
            raise ValueError(f"Línea con ID {request.line_id} no encontrada")

        # Línea tiene sesión activa?
        active_session = await self.session_repo.find_active_by_line(request.line_id)
        if active_session:
            raise ValueError(
                f"La línea {request.line_id} ya tiene una sesión activa "
                f"(session_id: {active_session.id})"
            )

        # Grupo existe?
        group = await self.cage_group_repo.find_by_id(
            CageGroupId.from_string(request.group_id)
        )
        if not group:
            raise ValueError(f"Grupo con ID {request.group_id} no encontrado")

        # Verificar que el request incluye exactamente las jaulas del grupo
        group_cage_ids = {str(cid.value) for cid in group.cage_ids}
        request_cage_ids = {cfg.cage_id for cfg in request.cage_configs}

        missing_in_request = group_cage_ids - request_cage_ids
        if missing_in_request:
            raise ValueError(
                f"Las siguientes jaulas del grupo no están en el request: "
                f"{', '.join(missing_in_request)}"
            )

        extra_in_request = request_cage_ids - group_cage_ids
        if extra_in_request:
            raise ValueError(
                f"Las siguientes jaulas del request no pertenecen al grupo: "
                f"{', '.join(extra_in_request)}"
            )

        # Doser existe en la línea?
        if not line.dosers:
            raise ValueError("La línea no tiene dosers configurados")
        selected_doser = line.get_doser_by_id(DoserId.from_string(request.doser_id))
        if not selected_doser:
            raise ValueError(
                f"El doser {request.doser_id} no existe en la línea {request.line_id}"
            )

        # Validar cada jaula
        cage_data = []
        for cfg in request.cage_configs:
            cage = await self.cage_repo.find_by_id(CageId.from_string(cfg.cage_id))
            if not cage:
                raise ValueError(f"Jaula con ID {cfg.cage_id} no encontrada")

            if cage.status == CageStatus.MAINTENANCE:
                raise ValueError(
                    f"La jaula {cage.name.value} está en mantenimiento y no puede ser alimentada"
                )

            assignment = await self.slot_assignment_repo.find_by_cage(
                CageId.from_string(cfg.cage_id)
            )
            if not assignment:
                raise ValueError(f"La jaula {cage.name.value} no está asignada a ninguna línea")
            if str(assignment.line_id) != request.line_id:
                raise ValueError(
                    f"La jaula {cage.name.value} está asignada a otra línea, "
                    f"no a {request.line_id}"
                )

            if cfg.mode != "FASTING":
                if cage.config.transport_time_seconds is None:
                    raise ValueError(
                        f"La jaula {cage.name.value} no tiene tiempo de transporte configurado. "
                        "Debe configurarlo antes de iniciar una alimentación cíclica."
                    )
                if cfg.rate_kg_per_min > selected_doser.max_rate_kg_per_min:
                    raise ValueError(
                        f"La tasa de la jaula {cage.name.value} ({cfg.rate_kg_per_min} kg/min) "
                        f"excede la capacidad máxima del doser "
                        f"({selected_doser.max_rate_kg_per_min} kg/min)"
                    )

            cage_data.append((cfg, cage, assignment))

        return line, group, selected_doser, cage_data
