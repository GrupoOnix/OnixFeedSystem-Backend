from datetime import datetime, timezone
from typing import Union

from api.models.feeding_models import CyclicFeedingRequest, ManualFeedingRequest
from api.models.system_config_models import ScheduleCheckResponse
from domain.enums import CageStatus
from domain.repositories import (
    ICageGroupRepository,
    ICageRepository,
    IFeedingLineRepository,
    IFeedingSessionRepository,
    ISlotAssignmentRepository,
    ISystemConfigRepository,
)
from domain.services.feeding_time_calculator import calculate_visit_duration
from domain.services.operating_schedule_service import OperatingScheduleService
from domain.value_objects import CageId, LineId
from domain.value_objects.identifiers import CageGroupId, DoserId


class CheckScheduleUseCase:

    def __init__(
        self,
        config_repository: ISystemConfigRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        cage_group_repository: ICageGroupRepository,
        slot_assignment_repository: ISlotAssignmentRepository,
        session_repository: IFeedingSessionRepository,
    ) -> None:
        self._config_repo = config_repository
        self._line_repo = line_repository
        self._cage_repo = cage_repository
        self._cage_group_repo = cage_group_repository
        self._slot_assignment_repo = slot_assignment_repository
        self._session_repo = session_repository

    async def execute(self, request: Union[ManualFeedingRequest, CyclicFeedingRequest]) -> ScheduleCheckResponse:
        if isinstance(request, ManualFeedingRequest):
            estimated_seconds = await self._calculate_manual_duration(request)
        else:
            estimated_seconds = await self._calculate_cyclic_duration(request)

        config = await self._config_repo.get()
        now_utc = datetime.now(timezone.utc)
        remaining_seconds = config.seconds_remaining_in_window(now_utc)
        fits = OperatingScheduleService(config).fits_in_window(estimated_seconds, now_utc)

        return ScheduleCheckResponse(
            fits=fits,
            estimated_seconds=estimated_seconds,
            estimated_minutes=round(estimated_seconds / 60, 2),
            remaining_seconds=remaining_seconds,
            remaining_minutes=round(remaining_seconds / 60, 2),
        )

    async def _calculate_manual_duration(self, request: ManualFeedingRequest) -> float:
        line = await self._line_repo.find_by_id(LineId.from_string(request.line_id))
        if not line:
            raise ValueError(f"Línea con ID {request.line_id} no encontrada")

        if not line.blower:
            raise ValueError(f"La línea {request.line_id} no tiene blower configurado")

        active_session = await self._session_repo.find_active_by_line(request.line_id)
        if active_session:
            raise ValueError(
                f"La línea {request.line_id} ya tiene una sesión activa "
                f"(session_id: {active_session.id})"
            )

        cage = await self._cage_repo.find_by_id(CageId.from_string(request.cage_id))
        if not cage:
            raise ValueError(f"Jaula con ID {request.cage_id} no encontrada")

        if cage.status == CageStatus.MAINTENANCE:
            raise ValueError(
                f"La jaula {cage.name.value} está en mantenimiento y no puede ser alimentada"
            )

        assignment = await self._slot_assignment_repo.find_by_cage(CageId.from_string(request.cage_id))
        if not assignment:
            raise ValueError(f"La jaula {cage.name.value} no está asignada a ninguna línea")
        if str(assignment.line_id) != request.line_id:
            raise ValueError(
                f"La jaula {cage.name.value} está asignada a otra línea, no a {request.line_id}"
            )

        if cage.config.transport_time_seconds is None:
            raise ValueError(
                f"La jaula {cage.name.value} no tiene tiempo de transporte configurado. "
                "Debe configurarlo antes de iniciar una alimentación."
            )

        if not line.dosers:
            raise ValueError("La línea no tiene dosers configurados")

        selected_doser = line.get_doser_by_id(DoserId.from_string(request.doser_id))
        if not selected_doser:
            raise ValueError(
                f"El doser {request.doser_id} no existe en la línea {request.line_id}"
            )

        if request.rate_kg_per_min > selected_doser.max_rate_kg_per_min:
            raise ValueError(
                f"La tasa solicitada ({request.rate_kg_per_min} kg/min) excede "
                f"la capacidad máxima del doser ({selected_doser.max_rate_kg_per_min} kg/min)"
            )

        estimated_seconds = calculate_visit_duration(
            quantity_kg=request.quantity_kg,
            rate_kg_per_min=request.rate_kg_per_min,
            transport_time_seconds=cage.config.transport_time_seconds,
            blower=line.blower,
        )

        return estimated_seconds

    async def _calculate_cyclic_duration(self, request: CyclicFeedingRequest) -> float:
        line = await self._line_repo.find_by_id(LineId.from_string(request.line_id))
        if not line:
            raise ValueError(f"Línea con ID {request.line_id} no encontrada")

        if not line.blower:
            raise ValueError(f"La línea {request.line_id} no tiene blower configurado")

        active_session = await self._session_repo.find_active_by_line(request.line_id)
        if active_session:
            raise ValueError(
                f"La línea {request.line_id} ya tiene una sesión activa "
                f"(session_id: {active_session.id})"
            )

        group = await self._cage_group_repo.find_by_id(
            CageGroupId.from_string(request.group_id)
        )
        if not group:
            raise ValueError(f"Grupo con ID {request.group_id} no encontrado")

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

        if not line.dosers:
            raise ValueError("La línea no tiene dosers configurados")
        selected_doser = line.get_doser_by_id(DoserId.from_string(request.doser_id))
        if not selected_doser:
            raise ValueError(
                f"El doser {request.doser_id} no existe en la línea {request.line_id}"
            )

        estimated_seconds = 0.0

        for cfg in request.cage_configs:
            if cfg.mode == "FASTING":
                continue

            cage = await self._cage_repo.find_by_id(CageId.from_string(cfg.cage_id))
            if not cage:
                raise ValueError(f"Jaula con ID {cfg.cage_id} no encontrada")

            if cage.status == CageStatus.MAINTENANCE:
                raise ValueError(
                    f"La jaula {cage.name.value} está en mantenimiento y no puede ser alimentada"
                )

            assignment = await self._slot_assignment_repo.find_by_cage(
                CageId.from_string(cfg.cage_id)
            )
            if not assignment:
                raise ValueError(f"La jaula {cage.name.value} no está asignada a ninguna línea")
            if str(assignment.line_id) != request.line_id:
                raise ValueError(
                    f"La jaula {cage.name.value} está asignada a otra línea, "
                    f"no a {request.line_id}"
                )

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

            kg_per_visit = round(cfg.quantity_kg / request.visits, 3)
            visit_seconds = calculate_visit_duration(
                quantity_kg=kg_per_visit,
                rate_kg_per_min=cfg.rate_kg_per_min,
                transport_time_seconds=cage.config.transport_time_seconds,
                blower=line.blower,
            )
            estimated_seconds += visit_seconds * request.visits

        return estimated_seconds
